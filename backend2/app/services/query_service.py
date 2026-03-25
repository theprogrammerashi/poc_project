import json
import json
import math

from app.core.prompts import INSIGHT_PROMPT, TITLE_PROMPT
from app.db.db import get_connection
from app.db.repository import get_messages, save_message, update_chat_title
from app.services.chart_service import build_visualizations, first_chart_axes
from app.services.sql_service import (
    describe_prefilters,
    generate_plan,
    generate_rule_based_sql,
    generate_sql,
    get_schema,
    get_schema_condensed,
)
from app.utils.context_builder import build_context


def _empty_response(
    answer,
    sql=None,
    data=None,
    chart=None,
    chart_type=None,
    x_key=None,
    y_key=None,
    visualizations=None,
):
    return {
        "answer": answer,
        "sql": sql,
        "data": data or [],
        "chart": chart,
        "chartType": chart_type,
        "xKey": x_key,
        "yKey": y_key,
        "visualizations": visualizations or [],
    }


def _clean_title(title, question):
    cleaned = " ".join(
        str(title or "").replace('"', " ").replace("'", " ").split()
    ).strip()
    if cleaned:
        return " ".join(cleaned.split()[:5])

    fallback = " ".join((question or "New Chat").split()[:5]).strip()
    return fallback or "New Chat"


def _format_result_preview(df, row_limit=10):
    if df is None or df.empty:
        return "(no rows)"
    return df.head(row_limit).to_string(index=False)


def _format_value(value):
    if value is None:
        return "None"
    if isinstance(value, float):
        if math.isnan(value):
            return "None"
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _format_column_name(column_name):
    name = str(column_name or "")
    if name.upper() in ["COUNT_STAR()", "COUNT(*)"]:
        return "Record Count"
    return name.replace("_", " ").title()


def _infer_result_label(columns):
    label_map = {
        "employee_name": "employees",
        "manager_name": "managers",
        "director_name": "directors",
        "supervisor_name": "supervisors",
        "quality_reviewer": "reviewers",
    }
    for entity_column, label in label_map.items():
        if entity_column in columns:
            return label
    return "audits"


def _build_data_table(df, row_limit=8):
    if df is None or df.empty:
        return "_No audits to display._"

    preview = df.head(row_limit)
    raw_headers = [str(col) for col in preview.columns if not str(col).startswith(("element_", "root_case_", "recommendations_"))]
    if len(raw_headers) > 8:
        raw_headers = raw_headers[:8]
        
    formatted_headers = [_format_column_name(col) for col in raw_headers]
    
    header_line = "| " + " | ".join(formatted_headers) + " |"
    divider_line = "| " + " | ".join(["---"] * len(formatted_headers)) + " |"
    body_lines = []

    for row in preview.to_dict(orient="records"):
        values = [str(_format_value(row.get(header))).replace("|", "/") for header in raw_headers]
        body_lines.append("| " + " | ".join(values) + " |")

    table_text = "\n".join([header_line, divider_line] + body_lines)
    if len(df) > row_limit:
        table_text += f"\n\nShowing the first **{row_limit}** audits out of **{len(df)}** total audits."
    return table_text


def _build_theoretical_answer(df, filter_text):
    if df is None or df.empty:
        return (
            "This request did not return any matching data for the current scope. "
            f"The applied filters were **{filter_text or 'None'}**."
        )

    columns = list(df.columns)
    result_label = _infer_result_label(columns)

    if "audit_month" in columns and "average_quality_score" in columns:
        return "This result shows how the average overall quality score changes month by month for the selected segment."
    if "element_name" in columns and "average_element_score" in columns:
        return "This result highlights the lowest-performing audit elements, so the lowest average scores indicate the strongest improvement opportunities."
    if all(column in columns for column in ["element_name", "root_cause", "recommendation", "impact_count"]):
        return "This result shows which root-cause and recommendation combinations are contributing most often to the weakest elements in scope."
    if "line_of_business" in columns and "total_audits" in columns:
        return "This result compares both audit volume and overall quality performance across line of business for the selected period."
    if "business_program" in columns and "quality_score_stddev" in columns:
        return "This result compares average quality performance and score variation across line of business and business program."
    if "most_frequent_underperforming_elements" in columns:
        return "This result identifies employees who stay below the threshold in the selected scope and shows the elements where they underperform most often."
    if len(columns) == 1:
        return f"This result returns the matching **{_format_column_name(columns[0])}** values for the requested question."
    return f"This result returns **{len(df)}** matching {result_label} for the requested analysis."


def _build_insight_bullets(df, filter_text):
    if df is None or df.empty:
        return [
            f'Applied filters: **{filter_text or "None"}**.',
            "The query ran successfully but no audits matched the request.",
        ]

    columns = list(df.columns)
    bullets = [f'Returned **{len(df)}** {_infer_result_label(columns)}.']

    if "audit_month" in columns and "average_quality_score" in columns:
        highest_row = df.loc[df["average_quality_score"].idxmax()]
        lowest_row = df.loc[df["average_quality_score"].idxmin()]
        bullets.append(
            f'Highest average quality score is **{_format_value(highest_row["average_quality_score"])}** in month **{_format_value(highest_row["audit_month"])}**.'
        )
        bullets.append(
            f'Lowest average quality score is **{_format_value(lowest_row["average_quality_score"])}** in month **{_format_value(lowest_row["audit_month"])}**.'
        )
    elif "element_name" in columns and "average_element_score" in columns:
        lowest_row = df.iloc[0]
        bullets.append(
            f'Lowest-scoring element is **{_format_value(lowest_row["element_name"])}** at **{_format_value(lowest_row["average_element_score"])}**.'
        )
        if len(df) > 1:
            second_row = df.iloc[1]
            bullets.append(
                f'The next weak element is **{_format_value(second_row["element_name"])}** at **{_format_value(second_row["average_element_score"])}**.'
            )
    elif all(column in columns for column in ["element_name", "root_cause", "recommendation", "impact_count"]):
        top_row = df.iloc[0]
        bullets.append(
            f'Top recurring issue is **{_format_value(top_row["root_cause"])}** for **{_format_value(top_row["element_name"])}**, with recommendation **{_format_value(top_row["recommendation"])}**.'
        )
        bullets.append(f'Highest observed impact count in this result is **{_format_value(top_row["impact_count"])}**.')
    elif "line_of_business" in columns and "average_quality_score" in columns:
        best_row = df.loc[df["average_quality_score"].idxmax()]
        bullets.append(
            f'Best average quality score is **{_format_value(best_row["average_quality_score"])}** for **{_format_value(best_row["line_of_business"])}**.'
        )
        if "total_audits" in columns:
            volume_row = df.loc[df["total_audits"].idxmax()]
            bullets.append(
                f'Highest audit volume is **{_format_value(volume_row["total_audits"])}** for **{_format_value(volume_row["line_of_business"])}**.'
            )
    elif "employee_name" in columns and "average_quality_score" in columns:
        lowest_row = df.loc[df["average_quality_score"].idxmin()]
        bullets.append(
            f'Lowest average quality score in this result is **{_format_value(lowest_row["average_quality_score"])}** for **{_format_value(lowest_row["employee_name"])}**.'
        )
    elif len(columns) == 1:
        sample_values = [_format_value(value) for value in df[columns[0]].head(3).tolist()]
        bullets.append(f'Example values include **{"**, **".join(sample_values)}**.')
    else:
        bullets.append(f'The result contains **{len(columns)}** columns: **{", ".join(columns[:5])}**.')

    if filter_text:
        bullets.append(f'Applied filters: **{filter_text}**.')

    return bullets[:4]


def _build_follow_ups(df):
    if df is None or df.empty:
        return [
            "Try the same question with a broader quarter, month, or program scope.",
            "Check whether the business value or filter wording matches the dataset exactly.",
            "Ask for a comparison view to identify where matching data does exist.",
        ]

    columns = list(df.columns)

    if "audit_month" in columns and "average_quality_score" in columns:
        ordered = df.sort_values("audit_month").reset_index(drop=True)
        largest_change = None
        for idx in range(1, len(ordered)):
            previous_row = ordered.iloc[idx - 1]
            current_row = ordered.iloc[idx]
            change_value = abs(
                float(current_row["average_quality_score"])
                - float(previous_row["average_quality_score"])
            )
            if largest_change is None or change_value > largest_change[0]:
                largest_change = (change_value, previous_row, current_row)
        return [
            (
                f'Why did the score move from month **{_format_value(largest_change[1]["audit_month"])}** '
                f'at **{_format_value(largest_change[1]["average_quality_score"])}** to month '
                f'**{_format_value(largest_change[2]["audit_month"])}** at '
                f'**{_format_value(largest_change[2]["average_quality_score"])}**?'
            )
            if largest_change
            else "Show the detailed month-by-month score movement for this segment.",
            "Break this monthly trend by line of business to see which segment is driving the movement.",
            "Show the same trend by supervisor or reviewer for the same scope.",
        ]

    if "element_name" in columns and "average_element_score" in columns:
        top_elements = [_format_value(value) for value in df["element_name"].head(3).tolist()]
        return [
            f'Show root causes and recommendations for **{top_elements[0]}**.',
            f'Compare **{top_elements[0]}** against **{top_elements[1]}** and **{top_elements[2]}** over time.' if len(top_elements) >= 3 else f'Compare **{top_elements[0]}** over time.',
            "Break these weak elements down by supervisor or program to identify ownership.",
        ]

    if all(column in columns for column in ["element_name", "root_cause", "recommendation", "impact_count"]):
        top_row = df.iloc[0]
        return [
            f'Which supervisors or reviewers are most associated with the root cause **{_format_value(top_row["root_cause"])}**?',
            f'Show the trend of **{_format_value(top_row["element_name"])}** over time to see whether the issue is improving or worsening.',
            "Compare the top root causes across line of business or program for the same scope.",
        ]

    if "line_of_business" in columns and "average_quality_score" in columns:
        best_row = df.loc[df["average_quality_score"].idxmax()]
        return [
            f'Compare the other segments against **{_format_value(best_row["line_of_business"])}**, which is currently the strongest performer in this result.',
            "Break this view down by business program to see where the score variation is coming from.",
            "Show the same distribution for the previous quarter to confirm whether this pattern is stable.",
        ]

    if "employee_name" in columns and "average_quality_score" in columns:
        lowest_row = df.loc[df["average_quality_score"].idxmin()]
        return [
            f'Show a detailed record-level view for **{_format_value(lowest_row["employee_name"])}**.',
            "Group these employees by manager or supervisor to see where coaching should start.",
            "Show which elements appear most often across the lowest-scoring employees in this result.",
        ]

    if len(columns) == 1:
        return [
            f'Show these **{_format_column_name(columns[0])}** with their quality scores.',
            "Count how many records are associated with each value in this list.",
            "Break this list down by month, quarter, or program.",
        ]

    return [
        "Rank the returned audits from best to worst on the key numeric metric.",
        "Break this same result down by quarter, line of business, or program.",
        "Show the record-level detail behind the lowest-performing part of this result.",
    ]


def _build_exact_answer(question, df, filter_text):
    if df is None:
        return None

    if df.empty:
        return (
            "## Answer\n"
            + _build_theoretical_answer(df, filter_text)
            + "\n\n## Key Insights\n"
            + "\n".join(f"- {line}" for line in _build_insight_bullets(df, filter_text))
            + "\n\n## Suggested Follow-ups\n"
            + "\n".join(f"{idx}. {line}" for idx, line in enumerate(_build_follow_ups(df), start=1))
        )

    columns = list(df.columns)
    theory_text = _build_theoretical_answer(df, filter_text)
    insight_text = "\n".join(f"- {line}" for line in _build_insight_bullets(df, filter_text))
    table_text = _build_data_table(df)
    follow_up_text = "\n".join(
        f"{idx}. {line}" for idx, line in enumerate(_build_follow_ups(df), start=1)
    )

    return (
        "## Answer\n"
        + theory_text
        + "\n\n## Key Insights\n"
        + insight_text
        + "\n\n## Data Table\n"
        + table_text
        + "\n\n## Suggested Follow-ups\n"
        + follow_up_text
    )


def _build_chart_artifacts(df):
    if df is None or df.empty or df.shape[1] < 2:
        return None, None, None, None, []

    visualizations = build_visualizations(df)
    chart_type, x_col, y_col = first_chart_axes(visualizations)
    return None, chart_type, x_col, y_col, visualizations


def handle_query(chat_id, question, preFilters, llm):
    question = (question or "").strip()
    if not question:
        return _empty_response("Please enter a question so I can analyze the audit data.")

    save_message(chat_id, "user", question)
    history = get_messages(chat_id)
    context = build_context(history[:-1])
    filter_text = describe_prefilters(preFilters)

    if len(history) == 1:
        try:
            title = llm.generate(
                [
                    {"role": "system", "content": TITLE_PROMPT},
                    {"role": "user", "content": question},
                ]
            )
            update_chat_title(chat_id, _clean_title(title, question))
        except Exception:
            update_chat_title(chat_id, _clean_title(question, question))

    intent_messages = [
        {
            "role": "system",
            "content": """
You are a router for a clinical audit analytics assistant.

Reply with only one word:
- DATABASE: if the user wants analysis, metrics, trends, comparisons, counts, root causes, recommendations, or anything that should inspect the audits dataset.
- CONVERSATION: if the user is greeting, chatting casually, or asking a general assistant question that does not need data.
""".strip(),
        },
        {"role": "user", "content": question},
    ]
    intent = llm.generate(intent_messages).strip().upper()

    if intent.startswith("CONVERSATION"):
        conv_sys = """
You are a helpful Clinical Audit AI Assistant.

Respond warmly in Markdown, keep it short, and guide the user toward useful analysis.
End with exactly this section:

## Suggested Follow-ups
1. ...
2. ...
3. ...
""".strip()
        conv_messages = [{"role": "system", "content": conv_sys}]
        conv_messages.extend(context)
        conv_messages.append({"role": "user", "content": question})

        answer = llm.generate(conv_messages)
        save_message(chat_id, "assistant", answer, None, None)
        return _empty_response(answer)

    plan = None
    sql = generate_rule_based_sql(question, prefilters=preFilters)

    if not sql:
        plan = generate_plan(llm, question, context=context, prefilters=preFilters)
        sql = generate_sql(
            llm,
            question,
            plan=plan,
            prefilters=preFilters,
            context=context,
        )

    try:
        with get_connection() as con:
            df = con.execute(sql).df()
    except Exception as error:
        try:
            sql = generate_sql(
                llm,
                question,
                plan=plan,
                error=str(error),
                prefilters=preFilters,
                context=context,
            )
            with get_connection() as con:
                df = con.execute(sql).df()
        except Exception:
            answer = (
                "I could not complete that analysis safely. Please rephrase the request "
                "or narrow it with a quarter, line of business, or program filter."
            )
            save_message(chat_id, "assistant", answer, sql, None)
            return _empty_response(answer, sql=sql)

    chart_path, chart_type, x_col, y_col, visualizations = _build_chart_artifacts(df)
    schema = get_schema_condensed()

    # Aggressively slice 150+ columns into a tiny payload to prevent history context ballooning on follow-ups
    json_columns = [col for col in df.columns if not str(col).startswith(("element_", "root_case_", "recommendations_"))]
    if len(json_columns) > 8:
        json_columns = json_columns[:8]
        
    result_records = df[json_columns].head(6).to_dict(orient="records")
    messages = [
        {
            "role": "system",
            "content": INSIGHT_PROMPT + f"\n\nDatabase Schema:\n{schema}",
        },
        {
            "role": "user",
            "content": f"""
Question:
{question}

Applied Filters:
{filter_text or "None"}

SQL Query:
{sql}

Columns:
{list(df.columns)}

Exact Result Records:
{json.dumps(result_records, default=str)}

Row Count:
{len(df)}
""".strip(),
        },
    ]

    answer = llm.generate(messages)
    save_message(chat_id, "assistant", answer, sql, chart_path)

    return _empty_response(
        answer,
        sql=sql,
        data=df.to_dict(orient="records"),
        chart=chart_path,
        chart_type=chart_type,
        x_key=x_col,
        y_key=y_col,
        visualizations=visualizations,
    )

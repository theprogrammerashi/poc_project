from app.db.repository import save_message, get_messages
from app.utils.context_builder import build_context
from app.services.sql_service import generate_sql
from app.services.chart_service import generate_chart
from app.db.db import get_connection
from app.core.prompts import INSIGHT_PROMPT
import json
from app.db.repository import update_chat_title
from app.core.prompts import TITLE_PROMPT

def handle_query(chat_id, question, preFilters, llm):

    # (Removed logic injecting preFilters into question to prevent SQL generation failures, per user request)

    # Save user message
    save_message(chat_id, "user", question)

    # Context
    history = get_messages(chat_id)
    
    # If first message → generate title 
    if len(history) == 1:  # only user message exists
        title_messages = [
        {"role": "system", "content": TITLE_PROMPT},
        {"role": "user", "content": question}
    ]

        title = llm.generate(title_messages)
        update_chat_title(chat_id, title)
    # Give context of previous messages only (exclude current question which is added in sql_service)
    context = build_context(history[:-1])

    # INTENT ROUTER
    intent_messages = [
        {"role": "system", "content": "You are a clinical audit query router. Read the user's message. Does it require querying the clinical audit database for statistics, trends, quality scores, employee metrics, or data? If YES, reply strictly with the single word 'DATABASE'. If it is a casual greeting, a meta-question about yourself, or general conversation, reply strictly with 'CONVERSATION'."},
        {"role": "user", "content": question}
    ]
    intent = llm.generate(intent_messages).strip().upper()

    if "CONVERSATION" in intent:
        conv_sys = "You are a helpful Clinical Audit AI Assistant. The user sent a conversational message. Greet them, ask how you can help, and suggest 3 example analytical questions they could ask about their clinical audit data (e.g. employee performance, root causes, quality trends). Format the response as a friendly markdown message. Provide EXACTLY 3 numbered suggestions under a 'Suggested Follow-ups' header."
        conv_messages = [{"role": "system", "content": conv_sys}]
        conv_messages.extend(context)
        conv_messages.append({"role": "user", "content": question})
        
        answer = llm.generate(conv_messages)
        save_message(chat_id, "assistant", answer, None, None)
        return {
            "answer": answer,
            "sql": None,
            "data": [],
            "chart": None,
            "chartType": None,
            "xKey": None,
            "yKey": None
        }

    # Generate SQL
    # STEP 1: Generate SQL (with context)
    sql = None
    sql = generate_sql(llm, question, context=context)

    # STEP 2: Execute with retry
    try:
        with get_connection() as con:
            df = con.execute(sql).df()
    except Exception as e:
        # Retry with error feedback
        try:
            sql = generate_sql(llm, question, context=context, error=str(e))
            with get_connection() as con:
                df = con.execute(sql).df()
        except Exception as retry_e:
            # Complete failure - handle gracefully without crashing backend
            answer = f"I'm sorry, I couldn't generate a valid SQL query to answer that question. It might involve columns or relationships not present in the database. (Error: {str(retry_e)})"
            save_message(chat_id, "assistant", answer, sql, None)
            return {
                "answer": answer,
                "sql": sql,
                "data": [],
                "chart": None,
                "chartType": None,
                "xKey": None,
                "yKey": None
            }

    # Chart
    # STEP: Ask LLM for chart decision
    chart_prompt = f"""
    You are a data visualization expert.

    Given:
    Columns: {list(df.columns)}
    Sample Data:
    {df.head(5).to_string()}

    Suggest:
    - chart_type (bar, line, pie, scatter)
    - x column
    - y column

    Return in JSON:
    {{"chart": "", "x": "", "y": ""}}
    """

    chart_decision = llm.generate([{"role": "system", "content": chart_prompt}])

    try:
        if df.shape[1] >= 2:
            chart_info = json.loads(chart_decision)
            chart_path = generate_chart(df, chart_info)
            chart_type = chart_info.get("chart", "bar")
            x_col = chart_info.get("x", df.columns[0])
            y_col = chart_info.get("y", df.columns[1])
        else:
            chart_path = None
            chart_type = None
            x_col = None
            y_col = None
    except:
        chart_path = generate_chart(df)  # fallback
        chart_type = "bar" if df.shape[1] >= 2 else None
        x_col = df.columns[0] if df.shape[1] >= 2 else None
        y_col = df.columns[1] if df.shape[1] >= 2 else None

    # Answer generation (FIXED)
    messages = [
    {"role": "system", "content": INSIGHT_PROMPT},
    {
        "role": "user",
        "content": f"""
        Question:
        {question}

        SQL Query:
        {sql}

        Columns:
        {list(df.columns)}

        Result:
        {df.head(10).to_string()}

        Row Count:
        {len(df)}
            """
    }
]

    answer = llm.generate(messages)

    # Save assistant message
    save_message(chat_id, "assistant", answer, sql, chart_path)

    return {
        "answer": answer,
        "sql": sql,
        "data": df.to_dict(orient="records"),
        "chart": chart_path,
        "chartType": chart_type,
        "xKey": x_col,
        "yKey": y_col
    }
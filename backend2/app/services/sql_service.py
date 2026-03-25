import csv
import difflib
import json
import re
from pathlib import Path

from app.core.prompts import SQL_PROMPT
from app.db.db import ANALYTICS_VIEW, RAW_TABLE, get_connection
from app.services.question_bank_rules import generate_question_bank_sql

SCHEMA_CACHE = None
SCHEMA_METADATA_CACHE = None
DISTINCT_VALUE_CACHE = {}

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
QUERY_TABLE = ANALYTICS_VIEW

FRONTEND_FILTER_MAP = {
    "quarter": "quarter",
    "lineOfBusiness": "line_of_business",
    "program": "business_program",
}

ENTITY_KEYWORDS = [
    ("supervisor email", "supervisor_email"),
    ("supervisors", "supervisor_name"),
    ("supervisor", "supervisor_name"),
    ("managers", "manager_name"),
    ("manager", "manager_name"),
    ("directors", "director_name"),
    ("director", "director_name"),
    ("reviewers", "quality_reviewer"),
    ("reviewer", "quality_reviewer"),
    ("employees", "employee_name"),
    ("employess", "employee_name"),
    ("employes", "employee_name"),
    ("employee", "employee_name"),
]

QUESTION_HINT_MAP = {
    "manager": 'Use "manager_name" for manager analysis.',
    "director": 'Use "director_name" for director analysis.',
    "supervisor email": 'Use "supervisor_email" for supervisor email.',
    "supervisor": 'Use "supervisor_name" for supervisor analysis.',
    "line of business": 'Use "line_of_business" or "line_of_business_name" for line of business.',
    "lob": 'Use "line_of_business" or "line_of_business_name" for line of business.',
    "program": 'Use "business_program" or "program_name" for program.',
    "business area": 'Use "business_program" or "program_name" when the user says business area.',
    "quality score": 'Use "quality_score_overall" or "overall_quality_score" for overall score.',
    "scores": 'If the user says scores without naming a specific metric, use "quality_score_overall".',
    "score": 'If the user says score without naming a specific metric, use "quality_score_overall".',
    "overall score": 'Use "quality_score_overall" or "overall_quality_score" for overall score.',
    "month": 'Use "month_audited" or "audit_month" for audit month.',
    "reviewer": 'Use "quality_reviewer" for reviewer.',
    "employees": 'If the user asks for employees, return distinct "employee_name" values unless they ask for records or cases.',
    "employee": 'If the user asks for employees, return distinct "employee_name" values unless they ask for records or cases.',
    "records": 'If the user asks for records, rows, cases, or audits, operate at the case/record grain.',
    "cases": 'If the user asks for records, rows, cases, or audits, operate at the case/record grain.',
}

ANALYTICS_ALIAS_COLUMNS = [
    {
        "name": "manager_name",
        "type": "VARCHAR",
        "description": 'Normalized alias for "employee_mananger". Use this for manager-level analysis.',
    },
    {
        "name": "director_name",
        "type": "VARCHAR",
        "description": 'Normalized alias for "emloyee_director". Use this for director-level analysis.',
    },
    {
        "name": "supervisor_name",
        "type": "VARCHAR",
        "description": 'Normalized alias for "employee_supervisor_name".',
    },
    {
        "name": "supervisor_email",
        "type": "VARCHAR",
        "description": 'Normalized alias for "employee_supervisor_email".',
    },
    {
        "name": "audit_month",
        "type": "INTEGER",
        "description": 'Normalized alias for "month_audited".',
    },
    {
        "name": "review_status",
        "type": "VARCHAR",
        "description": 'Normalized alias for "quality_review_status".',
    },
    {
        "name": "overall_quality_score",
        "type": "DOUBLE",
        "description": 'Normalized alias for "quality_score_overall".',
    },
    {
        "name": "line_of_business_name",
        "type": "VARCHAR",
        "description": 'Normalized alias for "line_of_business".',
    },
    {
        "name": "program_name",
        "type": "VARCHAR",
        "description": 'Normalized alias for "business_program".',
    },
]


def build_filter_conditions(prefilters):
    conditions = []
    params = []

    if not isinstance(prefilters, dict):
        return conditions, params

    for frontend_key, db_column in FRONTEND_FILTER_MAP.items():
        value = prefilters.get(frontend_key)
        if value in (None, "", "All"):
            continue
        conditions.append(f'"{db_column}" = ?')
        params.append(value)

    return conditions, params


def describe_prefilters(prefilters):
    if not isinstance(prefilters, dict):
        return ""

    lines = []
    for frontend_key, db_column in FRONTEND_FILTER_MAP.items():
        value = prefilters.get(frontend_key)
        if value in (None, "", "All"):
            continue
        lines.append(f'- "{db_column}" must equal "{value}"')

    return "\n".join(lines)


def _schema_json_candidates():
    return [
        BACKEND_DIR / "app" / "core" / "schema.json",
        BACKEND_DIR / "core" / "schema.json",
        BACKEND_DIR.parent / "schema.json",
        BACKEND_DIR / "schema.json",
    ]


def _schema_description():
    return (
        f"{QUERY_TABLE} is the normalized analytics view for the clinical audit dataset. "
        "One row still represents one audited case/record. Employees, managers, directors, "
        "reviewers, and supervisors can appear in multiple rows over time. Use DISTINCT for "
        "people lists and counts unless the user explicitly asks for records, rows, cases, or audits."
    )


def _build_schema_payload(table_name, description, columns):
    lines = [f"Table: {table_name}", f"Description: {description}", "Columns:"]
    normalized_columns = []
    seen = set()

    for column in columns:
        name = column.get("name")
        if not name or name in seen:
            continue
        seen.add(name)

        dtype = column.get("type", "UNKNOWN")
        details = column.get("description", "").strip() or _derive_column_description(name)
        line = f'- "{name}" ({dtype})'
        if details:
            line = f"{line}: {details}"
        lines.append(line)
        normalized_columns.append(
            {"name": name, "type": dtype, "description": details}
        )

    return {"schema_text": "\n".join(lines), "columns": normalized_columns}


def _derive_column_description(column_name):
    if column_name == "employee_name":
        return "Employee name. Employees can appear in multiple audit records, so use DISTINCT for employee lists/counts."
    if column_name == "manager_name":
        return 'Normalized manager name alias derived from the raw "employee_mananger" column.'
    if column_name == "director_name":
        return 'Normalized director name alias derived from the raw "emloyee_director" column.'
    if column_name == "supervisor_name":
        return "Normalized supervisor name alias."
    if column_name == "supervisor_email":
        return "Normalized supervisor email alias."
    if column_name == "employee_mananger":
        return "Raw manager column with a source-system typo. Prefer manager_name."
    if column_name == "emloyee_director":
        return "Raw director column with a source-system typo. Prefer director_name."
    if column_name in {"quality_score_overall", "overall_quality_score"}:
        return "Overall audit quality score for a case. Use this when the user says score/scores without naming a specific element."
    if column_name in {"month_audited", "audit_month"}:
        return "Audit month number."
    if column_name in {"line_of_business", "line_of_business_name"}:
        return "Line of business such as Medicare, DSNP, Commercial, or IFP."
    if column_name in {"business_program", "program_name"}:
        return "Business program under which the case was processed."
    if column_name in {"quality_review_status", "review_status"}:
        return "Lifecycle status of the audit."
    if column_name.startswith("element_"):
        return (
            "Element-level audit score for "
            + column_name.replace("element_", "").replace("_", " ")
            + ". Use this only when the user names that specific element."
        )
    if column_name.startswith("root_case_"):
        return (
            "Root cause text for "
            + column_name.replace("root_case_", "").replace("_", " ")
            + "."
        )
    if column_name.startswith("recommendations_"):
        return (
            "Recommended action for "
            + column_name.replace("recommendations_", "").replace("_", " ")
            + "."
        )
    return ""


def _load_schema_json():
    for path in _schema_json_candidates():
        if not path.exists():
            continue

        with path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    return {}


def _json_column_lookup():
    schema_json = _load_schema_json()
    lookup = {}
    for column in schema_json.get("columns", []):
        name = column.get("name")
        if not name:
            continue
        lookup[name] = {
            "name": name,
            "type": column.get("type", "UNKNOWN"),
            "description": column.get("description", ""),
        }
    for column in ANALYTICS_ALIAS_COLUMNS:
        lookup[column["name"]] = column
    return lookup


def _load_schema_from_database():
    try:
        with get_connection() as con:
            rows = con.execute(f"DESCRIBE {QUERY_TABLE}").fetchall()
    except Exception:
        try:
            with get_connection() as con:
                rows = con.execute(f"DESCRIBE {RAW_TABLE}").fetchall()
        except Exception:
            return None

    lookup = _json_column_lookup()
    columns = []
    for row in rows:
        column_name = row[0]
        source = lookup.get(column_name, {})
        columns.append(
            {
                "name": column_name,
                "type": source.get("type") or row[1],
                "description": source.get("description", ""),
            }
        )

    for alias_column in ANALYTICS_ALIAS_COLUMNS:
        if alias_column["name"] not in {column["name"] for column in columns}:
            columns.append(alias_column)

    return _build_schema_payload(
        QUERY_TABLE,
        _schema_description(),
        columns,
    )


def _load_schema_from_csv():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        return None

    with csv_files[0].open("r", encoding="utf-8", newline="") as file_handle:
        reader = csv.reader(file_handle)
        header = next(reader, [])

    lookup = _json_column_lookup()
    columns = []
    for name in header:
        source = lookup.get(name, {})
        columns.append(
            {
                "name": name,
                "type": source.get("type", "UNKNOWN"),
                "description": source.get("description", ""),
            }
        )

    columns.extend(ANALYTICS_ALIAS_COLUMNS)
    return _build_schema_payload(
        QUERY_TABLE,
        _schema_description(),
        columns,
    )


def get_schema_metadata():
    global SCHEMA_CACHE, SCHEMA_METADATA_CACHE

    if SCHEMA_METADATA_CACHE:
        return SCHEMA_METADATA_CACHE

    schema_payload = (
        _load_schema_from_database()
        or _load_schema_from_csv()
        or _build_schema_payload(QUERY_TABLE, _schema_description(), ANALYTICS_ALIAS_COLUMNS)
    )

    SCHEMA_METADATA_CACHE = schema_payload
    SCHEMA_CACHE = schema_payload["schema_text"]
    return SCHEMA_METADATA_CACHE


def get_schema():
    global SCHEMA_CACHE

    if SCHEMA_CACHE:
        return SCHEMA_CACHE

    SCHEMA_CACHE = get_schema_metadata()["schema_text"]
    return SCHEMA_CACHE


def get_schema_condensed():
    metadata = get_schema_metadata()
    lines = []
    
    seen_elements = False
    seen_roots = False
    seen_recs = False
    
    for c in metadata.get("columns", []):
        name = c.get("name", "")
        dtype = c.get("type", "UNKNOWN")
        desc = c.get("description", "")
        
        if name.startswith("element_"):
            if not seen_elements:
                lines.append('- "element_[X]" (DOUBLE): Contains the individual audit score for the given specific clinical element. Use this when the user names a specific clinical criteria.')
                seen_elements = True
            continue
        if name.startswith("root_case_"):
            if not seen_roots:
                lines.append('- "root_case_[X]" (VARCHAR): Contains the root cause string for a given element penalty.')
                seen_roots = True
            continue
        if name.startswith("recommendations_"):
            if not seen_recs:
                lines.append('- "recommendations_[X]" (VARCHAR): Contains the specific corrective action corresponding to a root cause.')
                seen_recs = True
            continue
            
        lines.append(f'- "{name}" ({dtype}): {desc}')
        
    return "Columns:\n" + "\n".join(lines)


def _format_context(context):
    if not context:
        return ""

    lines = []
    for message in context[-6:]:
        role = str(message.get("role", "user")).strip().upper()
        content = " ".join(str(message.get("content", "")).split())
        if not content:
            continue
        lines.append(f"{role}: {content[:300]}")

    return "\n".join(lines)


def _question_hints(question):
    lowered = str(question or "").lower()
    hints = []

    for phrase, hint in QUESTION_HINT_MAP.items():
        if phrase in lowered and hint not in hints:
            hints.append(f"- {hint}")

    return "\n".join(hints)


def _element_topics():
    topics = []
    for column in get_schema_metadata()["columns"]:
        name = column.get("name", "")
        if name.startswith("element_"):
            topics.append(name[len("element_"):])
    return sorted(set(topics))


def _canonical_dimension_value(value):
    text = str(value or "").upper()
    text = text.replace("0", "O").replace("1", "I").replace("5", "S")
    return re.sub(r"[^A-Z0-9]+", "", text)


def _get_distinct_dimension_values(column_name):
    if column_name in DISTINCT_VALUE_CACHE:
        return DISTINCT_VALUE_CACHE[column_name]

    try:
        with get_connection() as con:
            rows = con.execute(
                f'''
                SELECT DISTINCT "{column_name}"
                FROM {QUERY_TABLE}
                WHERE COALESCE(TRIM(CAST("{column_name}" AS VARCHAR)), '') <> ''
                ORDER BY 1
                '''
            ).fetchall()
    except Exception:
        DISTINCT_VALUE_CACHE[column_name] = []
        return DISTINCT_VALUE_CACHE[column_name]

    DISTINCT_VALUE_CACHE[column_name] = [row[0] for row in rows if row and row[0] is not None]
    return DISTINCT_VALUE_CACHE[column_name]


def _normalize_dimension_value(column_name, raw_value):
    if not raw_value:
        return raw_value

    values = _get_distinct_dimension_values(column_name)
    if not values:
        return raw_value

    raw_clean = str(raw_value).strip()
    canonical_raw = _canonical_dimension_value(raw_clean)
    for value in values:
        if _canonical_dimension_value(value) == canonical_raw:
            return value

    close_matches = difflib.get_close_matches(
        canonical_raw,
        [_canonical_dimension_value(value) for value in values],
        n=1,
        cutoff=0.7,
    )
    if close_matches:
        match = close_matches[0]
        for value in values:
            if _canonical_dimension_value(value) == match:
                return value

    return raw_clean


def _sql_literal(value):
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)


def _build_where_clause(conditions, params):
    if not conditions:
        return ""

    formatted_conditions = []
    for condition, value in zip(conditions, params):
        formatted_conditions.append(condition.replace("?", _sql_literal(value), 1))
    return " WHERE " + " AND ".join(formatted_conditions)


def _normalize_query_table(sql):
    sql = re.sub(
        r'(?i)\bfrom\s+"?audits"?\b',
        f"FROM {QUERY_TABLE}",
        sql,
    )
    sql = re.sub(
        r'(?i)\bfrom\s+"?um_clinical_audit_2025_synthetic"?\b',
        f"FROM {QUERY_TABLE}",
        sql,
    )
    return sql


def _clean_sql(raw_sql):
    sql = (raw_sql or "").strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)

    match = re.search(r"\b(with|select)\b", sql, flags=re.IGNORECASE)
    if match:
        sql = sql[match.start():]

    sql = _normalize_query_table(sql)
    sql = sql.strip().rstrip(";")
    if ";" in sql:
        sql = sql.split(";", 1)[0].strip()

    lowered = sql.lower().lstrip()
    if not lowered.startswith(("select", "with")):
        raise ValueError(f"Invalid SQL generated: {sql}")

    if re.search(
        r"\b(insert|update|delete|drop|alter|create|truncate|copy|export|replace)\b",
        lowered,
    ):
        raise ValueError(f"Unsafe SQL generated: {sql}")

    return sql


def _extract_entity_column(question):
    lowered = str(question or "").lower()
    for phrase, column_name in ENTITY_KEYWORDS:
        if phrase in lowered:
            return column_name
    return None


def _mentions_record_grain(question):
    lowered = str(question or "").lower()
    return any(token in lowered for token in ["record", "records", "row", "rows", "case", "cases", "audit", "audits"])


def _mentions_generic_score(question):
    lowered = str(question or "").lower()
    if "score" not in lowered:
        return False
    explicit_metric_tokens = [
        "timely decisions",
        "fair determinations",
        "evidence based",
        "appropriate care",
        "clinical accuracy",
        "appeals resolution",
        "decision consistency",
        "denial rates",
        "reversal rates",
        "authorization turnaround",
        "peer review quality",
        "documentation completeness",
        "patient safety",
        "adverse events",
    ]
    return not any(token in lowered for token in explicit_metric_tokens)


def _extract_score_threshold(question):
    if not _mentions_generic_score(question):
        return None

    patterns = [
        (r"\bbelow\s+(\d+(?:\.\d+)?)", "<"),
        (r"\bbelow\s+(?:the\s+)?(?:defined\s+)?threshold(?:\s+value)?(?:\s+of)?\s+(\d+(?:\.\d+)?)", "<"),
        (r"\bunder\s+(\d+(?:\.\d+)?)", "<"),
        (r"\bunder\s+(?:the\s+)?(?:defined\s+)?threshold(?:\s+value)?(?:\s+of)?\s+(\d+(?:\.\d+)?)", "<"),
        (r"\bless than\s+(\d+(?:\.\d+)?)", "<"),
        (r"\bless than\s+(?:the\s+)?(?:defined\s+)?threshold(?:\s+value)?(?:\s+of)?\s+(\d+(?:\.\d+)?)", "<"),
        (r"\babove\s+(\d+(?:\.\d+)?)", ">"),
        (r"\babove\s+(?:the\s+)?(?:defined\s+)?threshold(?:\s+value)?(?:\s+of)?\s+(\d+(?:\.\d+)?)", ">"),
        (r"\bover\s+(\d+(?:\.\d+)?)", ">"),
        (r"\bover\s+(?:the\s+)?(?:defined\s+)?threshold(?:\s+value)?(?:\s+of)?\s+(\d+(?:\.\d+)?)", ">"),
        (r"\bgreater than\s+(\d+(?:\.\d+)?)", ">"),
        (r"\bgreater than\s+(?:the\s+)?(?:defined\s+)?threshold(?:\s+value)?(?:\s+of)?\s+(\d+(?:\.\d+)?)", ">"),
        (r"\bat least\s+(\d+(?:\.\d+)?)", ">="),
        (r"\bat most\s+(\d+(?:\.\d+)?)", "<="),
        (r"\bthreshold(?:\s+value)?(?:\s+of)?\s+(\d+(?:\.\d+)?)", "="),
        (r"\bequal to\s+(\d+(?:\.\d+)?)", "="),
        (r"\b=\s*(\d+(?:\.\d+)?)", "="),
        (r"\b<\s*(\d+(?:\.\d+)?)", "<"),
        (r"\b>\s*(\d+(?:\.\d+)?)", ">"),
    ]

    lowered = str(question or "").lower()
    for pattern, operator in patterns:
        match = re.search(pattern, lowered)
        if match:
            return operator, match.group(1)

    return None


def _extract_text_filter(question, label):
    lowered = " ".join(str(question or "").split())
    escaped_label = re.escape(label)
    invalid_starts = {
        "and",
        "or",
        "with",
        "for",
        "in",
        "where",
        "under",
        "within",
        "including",
        "along",
        "who",
        "that",
        "which",
        "by",
    }
    patterns = [
        rf"(?:within|for|in|under)\s+{escaped_label}\s+([A-Za-z0-9&/_\- ]+?)(?:\s+(?:and|or|with|for|in|where|under|within|including|along|who|that|which|by)\b|[.,;:]|$)",
        rf"{escaped_label}\s+([A-Za-z0-9&/_\- ]+?)(?:\s+(?:and|or|with|for|in|where|under|within|including|along|who|that|which|by)\b|[.,;:]|$)",
        rf"{escaped_label}\s+is\s+([A-Za-z0-9&/_\- ]+?)(?:\s+(?:and|or|with|for|in|where|under|within|including|along|who|that|which|by)\b|[.,;:]|$)",
        rf"{escaped_label}\s*=\s*([A-Za-z0-9&/_\- ]+?)(?:\s+(?:and|or|with|for|in|where|under|within|including|along|who|that|which|by)\b|[.,;:]|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip().strip(".,")
            first_token = value.split()[0].lower() if value.split() else ""
            if first_token in invalid_starts or value.lower().startswith("the previous"):
                continue
            return value
    return None


def _extract_first_text_filter(question, labels):
    for label in labels:
        value = _extract_text_filter(question, label)
        if value:
            return value
    return None


def _extract_supervisor_filter(question):
    return _extract_first_text_filter(question, ["supervisor"])


def _extract_program_filter(question):
    return _extract_first_text_filter(question, ["business program", "business area", "program"])


def _build_common_conditions(question, prefilters=None):
    conditions = []
    params = []

    filter_conditions, filter_params = build_filter_conditions(prefilters)
    conditions.extend(filter_conditions)
    params.extend(filter_params)

    time_conditions, time_params = _extract_time_filters(question)
    conditions.extend(time_conditions)
    params.extend(time_params)

    supervisor_name = _extract_supervisor_filter(question)
    if supervisor_name:
        supervisor_name = _normalize_dimension_value("supervisor_name", supervisor_name)
        conditions.append('"supervisor_name" = ?')
        params.append(supervisor_name)

    program_name = _extract_program_filter(question)
    if program_name:
        program_name = _normalize_dimension_value("business_program", program_name)
        conditions.append('"business_program" = ?')
        params.append(program_name)

    line_of_business = _extract_text_filter(question, "line of business")
    if line_of_business:
        line_of_business = _normalize_dimension_value("line_of_business", line_of_business)
        conditions.append('"line_of_business" ILIKE ?')
        params.append(line_of_business)

    return conditions, params


def _generate_monthly_trend_sql(question, prefilters=None):
    lowered = str(question or "").lower()
    if "monthly trend" not in lowered or not _mentions_generic_score(question):
        return None

    conditions, params = _build_common_conditions(question, prefilters=prefilters)
    where_clause = _build_where_clause(conditions, params)
    return (
        'SELECT "audit_month", '
        'ROUND(AVG("quality_score_overall"), 2) AS "average_quality_score" '
        f'FROM {QUERY_TABLE}{where_clause} '
        'GROUP BY "audit_month" '
        'ORDER BY "audit_month"'
    )


def _generate_underperforming_elements_sql(question, prefilters=None):
    lowered = str(question or "").lower()
    if "underperforming elements" not in lowered:
        return None
    if "root cause" in lowered or "recommendation" in lowered:
        return None

    limit_match = re.search(r"\btop\s+(\d+)\b", lowered)
    limit_value = int(limit_match.group(1)) if limit_match else 5
    conditions, params = _build_common_conditions(question, prefilters=prefilters)
    where_clause = _build_where_clause(conditions, params)

    union_parts = []
    for topic in _element_topics():
        union_parts.append(
            'SELECT '
            + _sql_literal(topic)
            + ' AS "element_name", '
            + f'AVG("element_{topic}") AS "average_element_score" '
            + f'FROM {QUERY_TABLE}{where_clause}'
        )

    return (
        "WITH element_scores AS ("
        + " UNION ALL ".join(union_parts)
        + ') SELECT "element_name", '
        'ROUND("average_element_score", 2) AS "average_element_score" '
        'FROM element_scores '
        'ORDER BY "average_element_score" ASC, "element_name" '
        f"LIMIT {limit_value}"
    )


def _generate_root_cause_recommendation_sql(question, prefilters=None):
    lowered = str(question or "").lower()
    if "root cause" not in lowered or "recommend" not in lowered:
        return None
    if "underperforming elements" not in lowered:
        return None

    limit_match = re.search(r"\btop\s+(\d+)\s+root causes?\b", lowered)
    result_limit = int(limit_match.group(1)) if limit_match else 5
    element_limit_match = re.search(r"\btop\s+(\d+)\s+underperforming elements\b", lowered)
    element_limit = int(element_limit_match.group(1)) if element_limit_match else 3

    conditions, params = _build_common_conditions(question, prefilters=prefilters)
    where_clause = _build_where_clause(conditions, params)
    topics = _element_topics()

    score_parts = []
    impact_parts = []
    for topic in topics:
        score_parts.append(
            'SELECT '
            + _sql_literal(topic)
            + ' AS "element_name", '
            + f'AVG("element_{topic}") AS "average_element_score" '
            + f'FROM {QUERY_TABLE}{where_clause}'
        )
        impact_parts.append(
            'SELECT '
            + _sql_literal(topic)
            + ' AS "element_name", '
            + f'"root_case_{topic}" AS "root_cause", '
            + f'"recommendations_{topic}" AS "recommendation" '
            + f'FROM {QUERY_TABLE}{where_clause}'
        )

    return (
        "WITH element_scores AS ("
        + " UNION ALL ".join(score_parts)
        + '), top_elements AS ('
        + 'SELECT "element_name", ROUND("average_element_score", 2) AS "average_element_score" '
        + 'FROM element_scores ORDER BY "average_element_score" ASC, "element_name" '
        + f"LIMIT {element_limit}"
        + '), impact_details AS ('
        + " UNION ALL ".join(impact_parts)
        + ') SELECT i."element_name", i."root_cause", i."recommendation", COUNT(*) AS "impact_count" '
        + 'FROM impact_details AS i '
        + 'INNER JOIN top_elements AS t ON i."element_name" = t."element_name" '
        + 'WHERE COALESCE(TRIM(i."root_cause"), \'\') <> \'\' '
        + 'AND COALESCE(TRIM(i."recommendation"), \'\') <> \'\' '
        + 'GROUP BY i."element_name", i."root_cause", i."recommendation" '
        + 'ORDER BY "impact_count" DESC, i."element_name", i."root_cause" '
        + f"LIMIT {result_limit}"
    )


def _generate_previous_month_distribution_sql(question, prefilters=None):
    lowered = str(question or "").lower()
    if "distribution by line of business" not in lowered or "previous month" not in lowered:
        return None

    conditions, params = _build_common_conditions(question, prefilters=prefilters)
    where_clause = _build_where_clause(conditions, params)
    return (
        "WITH previous_month AS ("
        'SELECT "year", "month_audited" '
        f"FROM {QUERY_TABLE}{where_clause} "
        'GROUP BY "year", "month_audited" '
        'ORDER BY "year" DESC, "month_audited" DESC '
        'LIMIT 1 OFFSET 1'
        ') SELECT a."month_audited" AS "report_month", a."line_of_business", '
        'COUNT(*) AS "total_audits", '
        'ROUND(AVG(a."quality_score_overall"), 2) AS "average_quality_score" '
        f'FROM {QUERY_TABLE} AS a '
        'INNER JOIN previous_month AS p '
        'ON a."year" = p."year" AND a."month_audited" = p."month_audited" '
        'GROUP BY a."month_audited", a."line_of_business" '
        'ORDER BY "total_audits" DESC, a."line_of_business"'
    )


def _generate_previous_quarter_variation_sql(question, prefilters=None):
    lowered = str(question or "").lower()
    if "previous quarter" not in lowered:
        return None
    if "line of business" not in lowered or "business program" not in lowered:
        return None
    if not _mentions_generic_score(question):
        return None

    conditions, params = _build_common_conditions(question, prefilters=prefilters)
    where_clause = _build_where_clause(conditions, params)
    return (
        "WITH previous_quarter AS ("
        'SELECT "year", "quarter" '
        f"FROM {QUERY_TABLE}{where_clause} "
        'GROUP BY "year", "quarter" '
        'ORDER BY "year" DESC, "quarter" DESC '
        'LIMIT 1 OFFSET 1'
        ') SELECT a."quarter" AS "report_quarter", a."line_of_business", a."business_program", '
        'ROUND(AVG(a."quality_score_overall"), 2) AS "average_quality_score", '
        'ROUND(STDDEV_SAMP(a."quality_score_overall"), 2) AS "quality_score_stddev" '
        f'FROM {QUERY_TABLE} AS a '
        'INNER JOIN previous_quarter AS p '
        'ON a."year" = p."year" AND a."quarter" = p."quarter" '
        'GROUP BY a."quarter", a."line_of_business", a."business_program" '
        'ORDER BY a."line_of_business", a."business_program"'
    )


def _generate_consistently_below_threshold_sql(question, prefilters=None):
    lowered = str(question or "").lower()
    if "consistently" not in lowered or "underperform" not in lowered:
        return None
    if not any(token in lowered for token in ["employee", "employees", "employess", "employes"]):
        return None

    threshold_rule = _extract_score_threshold(question)
    threshold_value = float(threshold_rule[1]) if threshold_rule else 90.0
    conditions, params = _build_common_conditions(question, prefilters=prefilters)
    where_clause = _build_where_clause(conditions, params)
    topics = _element_topics()

    return (
        "WITH filtered AS ("
        + f'SELECT * FROM {QUERY_TABLE}{where_clause}'
        + '), consistent_employees AS ('
        + 'SELECT "employee_name", COUNT(*) AS "audit_count", '
        + 'ROUND(AVG("quality_score_overall"), 2) AS "average_quality_score", '
        + 'MAX("quality_score_overall") AS "max_quality_score" '
        + 'FROM filtered '
        + 'GROUP BY "employee_name" '
        + f'HAVING MAX("quality_score_overall") < {threshold_value}'
        + '), element_events AS ('
        + " UNION ALL ".join(
            [
                'SELECT "employee_name", '
                + _sql_literal(topic)
                + ' AS "element_name" '
                + 'FROM filtered '
                + f'WHERE "element_{topic}" < {threshold_value}'
                for topic in topics
            ]
        )
        + '), element_counts AS ('
        + 'SELECT e."employee_name", e."element_name", COUNT(*) AS "underperform_count", '
        + 'ROW_NUMBER() OVER (PARTITION BY e."employee_name" ORDER BY COUNT(*) DESC, e."element_name") AS "rn" '
        + 'FROM element_events AS e '
        + 'INNER JOIN consistent_employees AS c ON e."employee_name" = c."employee_name" '
        + 'GROUP BY e."employee_name", e."element_name" '
        + '), top_elements AS ('
        + 'SELECT "employee_name", '
        + 'STRING_AGG("element_name" || \' (\' || "underperform_count" || \')\', \', \' ORDER BY "underperform_count" DESC, "element_name") AS "most_frequent_underperforming_elements" '
        + 'FROM element_counts WHERE "rn" <= 3 GROUP BY "employee_name"'
        + ') SELECT c."employee_name", c."audit_count", c."average_quality_score", '
        + 'COALESCE(t."most_frequent_underperforming_elements", \'None\') AS "most_frequent_underperforming_elements" '
        + 'FROM consistent_employees AS c '
        + 'LEFT JOIN top_elements AS t ON c."employee_name" = t."employee_name" '
        + 'ORDER BY c."average_quality_score" ASC, c."audit_count" DESC, c."employee_name"'
    )


def _extract_time_filters(question):
    lowered = str(question or "").lower()
    conditions = []
    params = []
    month_name_map = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    quarter_match = re.search(r"\b(q[1-4])\b", lowered)
    if quarter_match:
        conditions.append('"quarter" = ?')
        params.append(quarter_match.group(1).upper())

    month_match = re.search(
        r"\b(?:for\s+)?month(?:\s+is|\s*=)?\s+([1-9]|1[0-2])\b", lowered
    )
    if month_match:
        conditions.append('"month_audited" = ?')
        params.append(month_match.group(1))
    else:
        for month_name, month_number in month_name_map.items():
            if re.search(rf"\b{month_name}\b", lowered):
                conditions.append('"month_audited" = ?')
                params.append(str(month_number))
                break

    year_match = re.search(r"\b(20\d{2})\b", lowered)
    if year_match:
        conditions.append('"year" = ?')
        params.append(year_match.group(1))

    return conditions, params


def generate_rule_based_sql(question, prefilters=None):
    question_bank_sql = generate_question_bank_sql(question)
    if question_bank_sql:
        return question_bank_sql

    specialized_handlers = [
        _generate_monthly_trend_sql,
        _generate_underperforming_elements_sql,
        _generate_root_cause_recommendation_sql,
        _generate_previous_month_distribution_sql,
        _generate_previous_quarter_variation_sql,
        _generate_consistently_below_threshold_sql,
    ]

    for handler in specialized_handlers:
        sql = handler(question, prefilters=prefilters)
        if sql:
            return sql

    entity_column = _extract_entity_column(question)
    score_rule = _extract_score_threshold(question)

    if not entity_column or not score_rule:
        return None

    conditions = []
    params = []

    filter_conditions, filter_params = build_filter_conditions(prefilters)
    conditions.extend(filter_conditions)
    params.extend(filter_params)

    time_conditions, time_params = _extract_time_filters(question)
    conditions.extend(time_conditions)
    params.extend(time_params)

    line_of_business = _extract_text_filter(question, "line of business")
    if line_of_business:
        conditions.append('"line_of_business" ILIKE ?')
        params.append(line_of_business)

    program_name = _extract_text_filter(question, "program")
    if program_name:
        conditions.append('"business_program" ILIKE ?')
        params.append(program_name)

    operator, threshold = score_rule
    conditions.append(f'"quality_score_overall" {operator} ?')
    params.append(threshold)

    where_clause = _build_where_clause(conditions, params)

    lowered = str(question or "").lower()
    if any(token in lowered for token in ["how many", "count", "number of"]):
        if _mentions_record_grain(question):
            return f'SELECT COUNT(*) AS matching_records FROM {QUERY_TABLE}{where_clause}'
        return f'SELECT COUNT(DISTINCT "{entity_column}") AS matching_{entity_column}s FROM {QUERY_TABLE}{where_clause}'

    if _mentions_record_grain(question):
        return f'SELECT * FROM {QUERY_TABLE}{where_clause}'

    return (
        f'SELECT DISTINCT "{entity_column}" '
        f'FROM {QUERY_TABLE}{where_clause} '
        f'ORDER BY "{entity_column}"'
    )


def generate_plan(llm, question, context=None, prefilters=None):
    context_text = _format_context(context)
    filter_text = describe_prefilters(prefilters)
    hint_text = _question_hints(question)

    messages = [
        {
            "role": "system",
            "content": f"""
You are a clinical audit query planner.

Available schema:
{get_schema_condensed()}

Rules:
- Plan against the normalized analytics view "{QUERY_TABLE}".
- Return 1 to 3 short steps.
- Use exact column names when you mention fields.
- Distinguish people from record grain.
- Do not write SQL.
- Respect any conversation context and active filters.
- Keep the plan practical and concise.
""".strip(),
        },
        {
            "role": "user",
            "content": "\n\n".join(
                part
                for part in [
                    f"Question:\n{question}",
                    f"Column hints:\n{hint_text}" if hint_text else "",
                    f"Recent context:\n{context_text}" if context_text else "",
                    f"Active filters:\n{filter_text}" if filter_text else "",
                ]
                if part
            ),
        },
    ]

    return llm.generate(messages)


def generate_sql(llm, question, plan=None, error=None, prefilters=None, context=None):
    system_prompt = SQL_PROMPT.format(schema=get_schema(), query_table=QUERY_TABLE)
    context_text = _format_context(context)
    filter_text = describe_prefilters(prefilters)
    hint_text = _question_hints(question)

    user_sections = [f"Question:\n{question}"]
    if hint_text:
        user_sections.append(f"Column hints:\n{hint_text}")
    if context_text:
        user_sections.append(f"Recent context:\n{context_text}")
    if filter_text:
        user_sections.append(
            "Required filters:\n"
            f"{filter_text}\nApply these filters inside the SQL query when relevant."
        )
    if plan:
        user_sections.append(f"Execution plan:\n{plan}")
    if error:
        user_sections.append(
            "Previous SQL error:\n"
            f"{error}\nRevise the query so it works in DuckDB with the same intent."
        )
    user_sections.append(f'Return one valid DuckDB query against "{QUERY_TABLE}".')

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(user_sections)},
    ]

    return _clean_sql(llm.generate(messages))

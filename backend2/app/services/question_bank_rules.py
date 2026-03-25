import re
from functools import lru_cache

from app.db.db import ANALYTICS_VIEW, get_connection

QUERY_TABLE = ANALYTICS_VIEW
DEFAULT_FAIL_THRESHOLD = 80
CRITICAL_ELEMENT_TOPICS = [
    "timely_decisions",
    "clinical_accuracy",
    "evidence_based_criteria",
    "patient_safety",
]


def _normalize_question(question):
    return " ".join(
        str(question or "")
        .replace("â€™", "'")
        .replace("â€”", "-")
        .replace("’", "'")
        .lower()
        .split()
    )


def _sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def _limitation_sql(message):
    return f"SELECT {_sql_literal(message)} AS limitation"


@lru_cache(maxsize=1)
def _element_topics():
    try:
        with get_connection() as con:
            rows = con.execute(f"DESCRIBE {QUERY_TABLE}").fetchall()
    except Exception:
        return []

    topics = []
    for row in rows:
        name = row[0]
        if name.startswith("element_"):
            topics.append(name[len("element_"):])
    return sorted(set(topics))


def _root_case_columns():
    return [f"root_case_{topic}" for topic in _element_topics()]


def _recommendation_columns():
    return [f"recommendations_{topic}" for topic in _element_topics()]


def _element_columns():
    return [f"element_{topic}" for topic in _element_topics()]


def _extract_named_id(question, prefix, canonical_prefix):
    match = re.search(rf"\b{prefix}[_ ]?(\d+)\b", _normalize_question(question))
    if not match:
        return None
    return f"{canonical_prefix}_{int(match.group(1))}"


def _extract_director(question):
    return _extract_named_id(question, "dir", "Dir")


def _extract_manager(question):
    return _extract_named_id(question, "mgr", "Mgr")


def _extract_supervisor(question):
    return _extract_named_id(question, "sup", "Sup")


def _extract_top_n(question, default=5):
    match = re.search(r"\btop\s+(\d+)\b", _normalize_question(question))
    if match:
        return int(match.group(1))
    return default


def _match_any_root_cause(value):
    clauses = [f'"{column}" = {_sql_literal(value)}' for column in _root_case_columns()]
    return "(" + " OR ".join(clauses) + ")"


def _match_any_recommendation(value):
    clauses = [
        f'"{column}" = {_sql_literal(value)}' for column in _recommendation_columns()
    ]
    return "(" + " OR ".join(clauses) + ")"


def _count_any_root_cause(value):
    parts = [
        f"CASE WHEN \"{column}\" = {_sql_literal(value)} THEN 1 ELSE 0 END"
        for column in _root_case_columns()
    ]
    return " + ".join(parts)


def _count_any_recommendation(value):
    parts = [
        f"CASE WHEN \"{column}\" = {_sql_literal(value)} THEN 1 ELSE 0 END"
        for column in _recommendation_columns()
    ]
    return " + ".join(parts)


def _any_root_recommendation_pair(root_value, recommendation_value):
    clauses = [
        f'("root_case_{topic}" = {_sql_literal(root_value)} AND "recommendations_{topic}" = {_sql_literal(recommendation_value)})'
        for topic in _element_topics()
    ]
    return "(" + " OR ".join(clauses) + ")"


def _nonperfect_element_count_expr():
    parts = [
        f'CASE WHEN "{column}" < 100 THEN 1 ELSE 0 END' for column in _element_columns()
    ]
    return " + ".join(parts)


def _compliance_100_count_expr():
    parts = [
        f'CASE WHEN "{column}" = 100 THEN 1 ELSE 0 END' for column in _element_columns()
    ]
    return " + ".join(parts)


def _element_score_union(
    where_sql="",
    extra_condition=None,
    include_app=False,
    include_supervisor=False,
):
    parts = []
    prefix_cols = []
    if include_app:
        prefix_cols.append('"application_name"')
    if include_supervisor:
        prefix_cols.append('"supervisor_name"')

    for topic in _element_topics():
        cols = []
        if prefix_cols:
            cols.extend(prefix_cols)
        cols.append(f"{_sql_literal(topic)} AS element_name")
        cols.append(f'"element_{topic}" AS element_score')

        where_parts = []
        if where_sql:
            where_parts.append(where_sql)
        if extra_condition:
            where_parts.append(extra_condition.format(topic=topic))
        where_clause = ""
        if where_parts:
            where_clause = " WHERE " + " AND ".join(where_parts)

        parts.append(f"SELECT {', '.join(cols)} FROM {QUERY_TABLE}{where_clause}")
    return " UNION ALL ".join(parts)


def _root_recommendation_union(
    where_sql="",
    extra_condition=None,
    include_app=False,
    include_supervisor=False,
    include_employee=False,
):
    parts = []
    prefix_cols = []
    if include_app:
        prefix_cols.append('"application_name"')
    if include_supervisor:
        prefix_cols.append('"supervisor_name"')
    if include_employee:
        prefix_cols.append('"employee_name"')

    for topic in _element_topics():
        cols = []
        if prefix_cols:
            cols.extend(prefix_cols)
        cols.extend(
            [
                f"{_sql_literal(topic)} AS element_name",
                f'"element_{topic}" AS element_score',
                f'"root_case_{topic}" AS root_cause',
                f'"recommendations_{topic}" AS recommendation',
            ]
        )

        where_parts = []
        if where_sql:
            where_parts.append(where_sql)
        if extra_condition:
            where_parts.append(extra_condition.format(topic=topic))
        where_clause = ""
        if where_parts:
            where_clause = " WHERE " + " AND ".join(where_parts)

        parts.append(f"SELECT {', '.join(cols)} FROM {QUERY_TABLE}{where_clause}")
    return " UNION ALL ".join(parts)


def _recommendation_event_union(where_sql=""):
    parts = []
    for topic in _element_topics():
        where_parts = []
        if where_sql:
            where_parts.append(where_sql)
        where_parts.append(f'COALESCE(TRIM("recommendations_{topic}"), \'\') <> \'\'')
        where_clause = " WHERE " + " AND ".join(where_parts)
        parts.append(
            "SELECT DISTINCT "
            + '"employee_name", "year", "month_audited", '
            + f'"recommendations_{topic}" AS recommendation '
            + f"FROM {QUERY_TABLE}{where_clause}"
        )
    return " UNION ALL ".join(parts)


def _question_file_one_sql(question, normalized):
    if 'the "quality gap" analysis' in normalized:
        return f"""
        WITH manager_scores AS (
            SELECT "director_name", "manager_name", AVG("quality_score_overall") AS manager_avg_score
            FROM {QUERY_TABLE}
            GROUP BY "director_name", "manager_name"
        )
        SELECT
            "director_name",
            ROUND(MAX(manager_avg_score), 2) AS highest_manager_average,
            ROUND(MIN(manager_avg_score), 2) AS lowest_manager_average,
            ROUND(MAX(manager_avg_score) - MIN(manager_avg_score), 2) AS performance_variance
        FROM manager_scores
        GROUP BY "director_name"
        ORDER BY performance_variance DESC, "director_name"
        LIMIT 1
        """

    if "top-tier supervisors" in normalized:
        director_name = _extract_director(question) or "Dir_10"
        return f"""
        SELECT
            "supervisor_name",
            COUNT(DISTINCT "employee_name") AS distinct_employees,
            ROUND(AVG("quality_score_overall"), 2) AS average_quality_score
        FROM {QUERY_TABLE}
        WHERE "director_name" = {_sql_literal(director_name)}
        GROUP BY "supervisor_name"
        HAVING COUNT(DISTINCT "employee_name") > 5
        ORDER BY average_quality_score DESC, "supervisor_name"
        LIMIT 1
        """

    if "managerial consistency" in normalized:
        return f"""
        WITH supervisor_scores AS (
            SELECT "manager_name", "supervisor_name", AVG("quality_score_overall") AS supervisor_avg_score
            FROM {QUERY_TABLE}
            GROUP BY "manager_name", "supervisor_name"
        )
        SELECT
            "manager_name",
            ROUND(STDDEV_SAMP(supervisor_avg_score), 2) AS supervisor_performance_stddev
        FROM supervisor_scores
        GROUP BY "manager_name"
        ORDER BY supervisor_performance_stddev DESC NULLS LAST, "manager_name"
        LIMIT 1
        """

    if "employee outliers" in normalized:
        manager_name = _extract_manager(question) or "Mgr_24"
        return f"""
        WITH employee_scores AS (
            SELECT "supervisor_name", "employee_name", AVG("quality_score_overall") AS employee_avg_score
            FROM {QUERY_TABLE}
            WHERE "manager_name" = {_sql_literal(manager_name)}
            GROUP BY "supervisor_name", "employee_name"
        ),
        supervisor_stats AS (
            SELECT
                "supervisor_name",
                AVG(employee_avg_score) AS supervisor_team_average,
                STDDEV_SAMP(employee_avg_score) AS supervisor_team_stddev
            FROM employee_scores
            GROUP BY "supervisor_name"
        )
        SELECT
            e."supervisor_name",
            e."employee_name",
            ROUND(e.employee_avg_score, 2) AS employee_average_score,
            ROUND(s.supervisor_team_average, 2) AS supervisor_team_average,
            ROUND(s.supervisor_team_stddev, 2) AS supervisor_team_stddev
        FROM employee_scores AS e
        INNER JOIN supervisor_stats AS s ON e."supervisor_name" = s."supervisor_name"
        WHERE e.employee_avg_score < s.supervisor_team_average - (2 * COALESCE(s.supervisor_team_stddev, 0))
        ORDER BY employee_average_score ASC, e."supervisor_name", e."employee_name"
        """

    if "departmental benchmarking" in normalized:
        manager_name = _extract_manager(question) or "Mgr_12"
        return f"""
        WITH manager_quarter AS (
            SELECT "quarter", AVG("quality_score_overall") AS manager_average_score
            FROM {QUERY_TABLE}
            WHERE "manager_name" = {_sql_literal(manager_name)}
            GROUP BY "quarter"
        ),
        company_quarter AS (
            SELECT "quarter", AVG("quality_score_overall") AS company_average_score
            FROM {QUERY_TABLE}
            GROUP BY "quarter"
        )
        SELECT
            m."quarter",
            ROUND(m.manager_average_score, 2) AS manager_average_score,
            ROUND(c.company_average_score, 2) AS company_average_score,
            ROUND(m.manager_average_score - c.company_average_score, 2) AS score_gap
        FROM manager_quarter AS m
        INNER JOIN company_quarter AS c ON m."quarter" = c."quarter"
        ORDER BY m."quarter"
        """

    if "succession planning" in normalized:
        limit_value = _extract_top_n(question, default=3)
        return f"""
        WITH manager_scores AS (
            SELECT "manager_name", AVG("quality_score_overall") AS manager_average_score
            FROM {QUERY_TABLE}
            GROUP BY "manager_name"
        ),
        lowest_manager AS (
            SELECT "manager_name"
            FROM manager_scores
            ORDER BY manager_average_score ASC, "manager_name"
            LIMIT 1
        )
        SELECT
            (SELECT "manager_name" FROM lowest_manager) AS manager_name,
            "supervisor_name",
            ROUND(AVG("quality_score_overall"), 2) AS supervisor_average_score
        FROM {QUERY_TABLE}
        WHERE "manager_name" = (SELECT "manager_name" FROM lowest_manager)
        GROUP BY "supervisor_name"
        ORDER BY supervisor_average_score DESC, "supervisor_name"
        LIMIT {limit_value}
        """

    if "span of control impact" in normalized:
        return f"""
        WITH supervisor_metrics AS (
            SELECT
                "supervisor_name",
                COUNT(DISTINCT "employee_name") AS team_size,
                AVG("element_documentation_completeness") AS average_documentation_completeness
            FROM {QUERY_TABLE}
            GROUP BY "supervisor_name"
        )
        SELECT
            ROUND(CORR(team_size, average_documentation_completeness), 4) AS correlation_coefficient,
            COUNT(*) AS supervisor_count,
            ROUND(AVG(team_size), 2) AS average_team_size,
            ROUND(AVG(average_documentation_completeness), 2) AS average_documentation_score
        FROM supervisor_metrics
        """

    if "management hierarchy audit" in normalized:
        return f"""
        WITH supervisor_scores AS (
            SELECT "manager_name", "supervisor_name", AVG("quality_score_overall") AS supervisor_average_score
            FROM {QUERY_TABLE}
            GROUP BY "manager_name", "supervisor_name"
        )
        SELECT
            "manager_name",
            ROUND(MAX(supervisor_average_score), 2) AS highest_supervisor_average,
            ROUND(MIN(supervisor_average_score), 2) AS lowest_supervisor_average
        FROM supervisor_scores
        GROUP BY "manager_name"
        HAVING MAX(supervisor_average_score) > 95 AND MIN(supervisor_average_score) < 70
        ORDER BY "manager_name"
        """

    if "systemic failures" in normalized:
        return f"""
        SELECT
            "root_case_timely_decisions" AS root_cause,
            COUNT(*) AS occurrence_count
        FROM {QUERY_TABLE}
        WHERE "element_timely_decisions" < 50
          AND COALESCE(TRIM("root_case_timely_decisions"), '') <> ''
        GROUP BY "root_case_timely_decisions"
        ORDER BY occurrence_count DESC, root_cause
        LIMIT 1
        """

    if "reeducation roi" in normalized:
        manager_name = _extract_manager(question) or "Mgr_24"
        return f"""
        SELECT
            "recommendations_clinical_accuracy" AS recommendation,
            COUNT(*) AS occurrence_count
        FROM {QUERY_TABLE}
        WHERE "manager_name" = {_sql_literal(manager_name)}
          AND COALESCE(TRIM("recommendations_clinical_accuracy"), '') <> ''
        GROUP BY "recommendations_clinical_accuracy"
        ORDER BY occurrence_count DESC, recommendation
        LIMIT 3
        """

    if "tool-specific issues" in normalized:
        return f"""
        SELECT
            "application_name",
            COUNT(*) AS occurrence_count
        FROM {QUERY_TABLE}
        WHERE "root_case_authorization_turnaround" = 'System'
        GROUP BY "application_name"
        ORDER BY occurrence_count DESC, "application_name"
        LIMIT 1
        """

    if 'the "training" trap' in normalized:
        condition = _any_root_recommendation_pair("Knowledge", "Training")
        return f"""
        WITH audit_flags AS (
            SELECT
                "record_id",
                "line_of_business",
                CASE WHEN {condition} THEN 1 ELSE 0 END AS matched_flag
            FROM {QUERY_TABLE}
        )
        SELECT
            "line_of_business",
            COUNT(*) AS total_audits,
            SUM(matched_flag) AS matched_audits,
            ROUND(100.0 * SUM(matched_flag) / COUNT(*), 2) AS matched_percentage
        FROM audit_flags
        GROUP BY "line_of_business"
        ORDER BY matched_percentage DESC, "line_of_business"
        LIMIT 1
        """

    if "automation opportunities" in normalized:
        recommendation_count = _count_any_recommendation("Automation")
        return f"""
        SELECT
            "director_name",
            SUM({recommendation_count}) AS automation_recommendation_count
        FROM {QUERY_TABLE}
        GROUP BY "director_name"
        ORDER BY automation_recommendation_count DESC, "director_name"
        LIMIT 1
        """

    if "process leakage" in normalized:
        return f"""
        SELECT
            "root_case_patient_safety" AS root_cause,
            COUNT(*) AS occurrence_count
        FROM {QUERY_TABLE}
        WHERE "element_patient_safety" < 100
          AND COALESCE(TRIM("root_case_patient_safety"), '') <> ''
        GROUP BY "root_case_patient_safety"
        ORDER BY occurrence_count DESC, root_cause
        LIMIT 3
        """

    if "effectiveness of feedback" in normalized:
        return f"""
        WITH employee_quarter_scores AS (
            SELECT
                "employee_name",
                "quarter",
                AVG("quality_score_overall") AS average_quality_score,
                MAX(CASE WHEN {_match_any_recommendation('Reeducation')} THEN 1 ELSE 0 END) AS received_reeducation
            FROM {QUERY_TABLE}
            WHERE "quarter" IN ('Q1', 'Q2')
            GROUP BY "employee_name", "quarter"
        ),
        q1 AS (
            SELECT "employee_name", average_quality_score AS q1_average_score
            FROM employee_quarter_scores
            WHERE "quarter" = 'Q1' AND received_reeducation = 1
        ),
        q2 AS (
            SELECT "employee_name", average_quality_score AS q2_average_score
            FROM employee_quarter_scores
            WHERE "quarter" = 'Q2'
        )
        SELECT
            q1."employee_name",
            ROUND(q1.q1_average_score, 2) AS q1_average_score,
            ROUND(q2.q2_average_score, 2) AS q2_average_score,
            ROUND(q2.q2_average_score - q1.q1_average_score, 2) AS score_change
        FROM q1
        INNER JOIN q2 ON q1."employee_name" = q2."employee_name"
        WHERE q2.q2_average_score <= q1.q1_average_score
        ORDER BY score_change ASC, q1."employee_name"
        """

    if "high-risk case detection" in normalized:
        return f"""
        SELECT
            "supervisor_name",
            "case_id",
            "element_patient_safety" AS patient_safety_score,
            "element_clinical_accuracy" AS clinical_accuracy_score
        FROM {QUERY_TABLE}
        WHERE "element_patient_safety" = 0 OR "element_clinical_accuracy" = 0
        ORDER BY "supervisor_name", "case_id"
        """

    if "lob performance tilt" in normalized:
        return f"""
        SELECT
            "line_of_business",
            ROUND(AVG("element_evidence_based_criteria"), 2) AS average_evidence_based_criteria_score,
            COUNT(*) AS audit_count
        FROM {QUERY_TABLE}
        GROUP BY "line_of_business"
        ORDER BY average_evidence_based_criteria_score DESC, "line_of_business"
        """

    if "reviewer calibration" in normalized:
        return f"""
        WITH reviewer_program AS (
            SELECT
                "quality_reviewer",
                "business_program",
                AVG("quality_score_overall") AS reviewer_average_score
            FROM {QUERY_TABLE}
            GROUP BY "quality_reviewer", "business_program"
        ),
        program_average AS (
            SELECT
                "business_program",
                AVG("quality_score_overall") AS program_average_score
            FROM {QUERY_TABLE}
            GROUP BY "business_program"
        )
        SELECT
            r."quality_reviewer",
            r."business_program",
            ROUND(r.reviewer_average_score, 2) AS reviewer_average_score,
            ROUND(p.program_average_score, 2) AS program_average_score,
            ROUND(r.reviewer_average_score - p.program_average_score, 2) AS score_gap
        FROM reviewer_program AS r
        INNER JOIN program_average AS p ON r."business_program" = p."business_program"
        WHERE r.reviewer_average_score < p.program_average_score
        ORDER BY score_gap ASC, r."quality_reviewer", r."business_program"
        """

    if "programmatic weakness" in normalized:
        return f"""
        SELECT
            "business_program",
            ROUND(AVG("element_decision_consistency"), 2) AS average_decision_consistency_score
        FROM {QUERY_TABLE}
        GROUP BY "business_program"
        ORDER BY average_decision_consistency_score ASC, "business_program"
        LIMIT 1
        """

    if "audit status bottleneck" in normalized:
        manager_name = _extract_manager(question) or "Mgr_12"
        return f"""
        WITH latest_month AS (
            SELECT MAX("month_audited") AS current_month FROM {QUERY_TABLE}
        )
        SELECT
            COUNT(*) AS active_case_count,
            ROUND(AVG((SELECT current_month FROM latest_month) - "month_audited"), 2) AS average_month_age
        FROM {QUERY_TABLE}
        WHERE "manager_name" = {_sql_literal(manager_name)}
          AND "quality_review_status" = 'Active'
        """

    if "monthly volatility" in normalized:
        return f"""
        WITH monthly_scores AS (
            SELECT "month_audited", AVG("element_documentation_completeness") AS monthly_average_score
            FROM {QUERY_TABLE}
            WHERE "year" = 2025
            GROUP BY "month_audited"
        ),
        score_deltas AS (
            SELECT
                "month_audited",
                monthly_average_score,
                monthly_average_score - LAG(monthly_average_score) OVER (ORDER BY "month_audited") AS score_change
            FROM monthly_scores
        )
        SELECT
            "month_audited",
            ROUND(monthly_average_score, 2) AS monthly_average_score,
            ROUND(score_change, 2) AS month_over_month_change
        FROM score_deltas
        WHERE score_change IS NOT NULL
        ORDER BY month_over_month_change ASC, "month_audited"
        LIMIT 1
        """

    if "critical element correlation" in normalized:
        return f"""
        SELECT
            ROUND(CORR("element_timely_decisions", "element_clinical_accuracy"), 4) AS correlation_coefficient,
            ROUND(AVG("element_timely_decisions"), 2) AS average_timely_decisions_score,
            ROUND(AVG("element_clinical_accuracy"), 2) AS average_clinical_accuracy_score
        FROM {QUERY_TABLE}
        """

    if 'the "fatigue" factor' in normalized:
        return f"""
        WITH month_groups AS (
            SELECT
                CASE
                    WHEN "month_audited" IN (1, 4, 7, 10) THEN 'Quarter Start'
                    WHEN "month_audited" IN (3, 6, 9, 12) THEN 'Quarter End'
                END AS month_group,
                "quality_score_overall"
            FROM {QUERY_TABLE}
            WHERE "month_audited" IN (1, 3, 4, 6, 7, 9, 10, 12)
        )
        SELECT
            month_group,
            ROUND(AVG("quality_score_overall"), 2) AS average_quality_score,
            COUNT(*) AS audit_count
        FROM month_groups
        GROUP BY month_group
        ORDER BY month_group
        """

    if "top talent identification" in normalized:
        return f"""
        SELECT
            "employee_name",
            COUNT(DISTINCT "month_audited") AS qualifying_months
        FROM {QUERY_TABLE}
        WHERE "element_clinical_accuracy" = 100
          AND "element_appropriate_care" = 100
          AND "element_evidence_based_criteria" = 100
        GROUP BY "employee_name"
        HAVING COUNT(DISTINCT "month_audited") > 1
        ORDER BY qualifying_months DESC, "employee_name"
        """

    if "resource reallocation" in normalized:
        documentation_count = _count_any_root_cause("Documentation")
        return f"""
        SELECT
            "director_name",
            SUM({documentation_count}) AS documentation_root_cause_count
        FROM {QUERY_TABLE}
        GROUP BY "director_name"
        ORDER BY documentation_root_cause_count DESC, "director_name"
        LIMIT 1
        """

    if "audit diversity" in normalized:
        union_sql = " UNION ALL ".join(
            [
                f'SELECT "employee_name", "{column}" AS root_cause FROM {QUERY_TABLE} WHERE COALESCE(TRIM("{column}"), \'\') <> \'\''
                for column in _root_case_columns()
            ]
        )
        return f"""
        WITH employee_root_causes AS (
            {union_sql}
        )
        SELECT
            "employee_name",
            COUNT(DISTINCT root_cause) AS distinct_root_cause_types
        FROM employee_root_causes
        GROUP BY "employee_name"
        ORDER BY distinct_root_cause_types DESC, "employee_name"
        LIMIT 1
        """

    if "program health" in normalized:
        element_count = len(_element_columns())
        compliance_count = _compliance_100_count_expr()
        return f"""
        SELECT
            "line_of_business",
            ROUND(100.0 * SUM({compliance_count}) / (COUNT(*) * {element_count}), 2) AS compliance_rate_percentage
        FROM {QUERY_TABLE}
        WHERE "line_of_business" IN ('Commercial', 'DSNP')
        GROUP BY "line_of_business"
        ORDER BY "line_of_business"
        """

    if "recommendation synergy" in normalized:
        return f"""
        WITH employee_monthly_scores AS (
            SELECT
                "employee_name",
                "year",
                "month_audited",
                AVG("quality_score_overall") AS monthly_average_score,
                MAX(CASE WHEN {_match_any_recommendation('Checklist')} THEN 1 ELSE 0 END) AS checklist_flag
            FROM {QUERY_TABLE}
            GROUP BY "employee_name", "year", "month_audited"
        ),
        sequenced AS (
            SELECT
                *,
                LEAD(monthly_average_score) OVER (PARTITION BY "employee_name" ORDER BY "year", "month_audited") AS next_month_average_score
            FROM employee_monthly_scores
        )
        SELECT
            "employee_name",
            "year",
            "month_audited",
            ROUND(monthly_average_score, 2) AS current_average_score,
            ROUND(next_month_average_score, 2) AS next_average_score,
            CASE
                WHEN next_month_average_score > monthly_average_score THEN 'Improved'
                WHEN next_month_average_score < monthly_average_score THEN 'Declined'
                ELSE 'No Change'
            END AS follow_up_result
        FROM sequenced
        WHERE checklist_flag = 1 AND next_month_average_score IS NOT NULL
        ORDER BY "employee_name", "year", "month_audited"
        """

    if "managerial oversight" in normalized:
        omission_flag = f"CASE WHEN {_match_any_root_cause('Omission')} THEN 1 ELSE 0 END"
        return f"""
        SELECT
            "manager_name",
            ROUND(100.0 * AVG({omission_flag}), 2) AS omission_case_percentage,
            COUNT(*) AS total_cases
        FROM {QUERY_TABLE}
        GROUP BY "manager_name"
        ORDER BY omission_case_percentage DESC, "manager_name"
        LIMIT 1
        """

    if "quality trend projection" in normalized:
        return f"""
        WITH quarterly_scores AS (
            SELECT
                "supervisor_name",
                CASE "quarter"
                    WHEN 'Q1' THEN 1
                    WHEN 'Q2' THEN 2
                    WHEN 'Q3' THEN 3
                    WHEN 'Q4' THEN 4
                END AS quarter_number,
                AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            WHERE "quarter" IN ('Q1', 'Q2', 'Q3')
            GROUP BY "supervisor_name", "quarter"
        ),
        trends AS (
            SELECT
                "supervisor_name",
                REGR_SLOPE(average_quality_score, quarter_number) AS slope,
                REGR_INTERCEPT(average_quality_score, quarter_number) AS intercept,
                COUNT(*) AS observed_quarters
            FROM quarterly_scores
            GROUP BY "supervisor_name"
        )
        SELECT
            "supervisor_name",
            ROUND(slope, 2) AS quarterly_slope,
            ROUND(intercept + (slope * 4), 2) AS projected_q4_average_score
        FROM trends
        WHERE observed_quarters = 3
          AND slope < 0
          AND intercept + (slope * 4) < 80
        ORDER BY projected_q4_average_score ASC, "supervisor_name"
        """

    return None


def _question_file_two_sql(question, normalized):
    low_score_threshold = 70

    if "which application name has the lowest average quality_score_overall" in normalized:
        union_sql = _root_recommendation_union(include_app=True)
        return f"""
        WITH lowest_app AS (
            SELECT
                "application_name",
                AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "application_name"
            ORDER BY average_quality_score ASC, "application_name"
            LIMIT 1
        ),
        root_causes AS (
            {union_sql}
        ),
        top_root_causes AS (
            SELECT
                "application_name",
                STRING_AGG(root_cause, ', ' ORDER BY root_cause_count DESC, root_cause) AS top_root_causes
            FROM (
                SELECT
                    "application_name",
                    root_cause,
                    COUNT(*) AS root_cause_count,
                    ROW_NUMBER() OVER (PARTITION BY "application_name" ORDER BY COUNT(*) DESC, root_cause) AS rn
                FROM root_causes
                WHERE COALESCE(TRIM(root_cause), '') <> ''
                GROUP BY "application_name", root_cause
            )
            WHERE rn <= 3
            GROUP BY "application_name"
        )
        SELECT
            l."application_name",
            ROUND(l.average_quality_score, 2) AS average_quality_score,
            COALESCE(t.top_root_causes, 'No root cause data') AS top_root_causes
        FROM lowest_app AS l
        LEFT JOIN top_root_causes AS t ON l."application_name" = t."application_name"
        """

    if "which supervisors consistently manage low-performing employees" in normalized:
        return f"""
        WITH employee_scores AS (
            SELECT
                "supervisor_name",
                "employee_name",
                AVG("quality_score_overall") AS employee_average_score
            FROM {QUERY_TABLE}
            GROUP BY "supervisor_name", "employee_name"
        )
        SELECT
            "supervisor_name",
            COUNT(*) AS total_employees,
            SUM(CASE WHEN employee_average_score < {DEFAULT_FAIL_THRESHOLD} THEN 1 ELSE 0 END) AS low_performing_employees,
            ROUND(100.0 * SUM(CASE WHEN employee_average_score < {DEFAULT_FAIL_THRESHOLD} THEN 1 ELSE 0 END) / COUNT(*), 2) AS low_performing_employee_rate
        FROM employee_scores
        GROUP BY "supervisor_name"
        ORDER BY low_performing_employee_rate DESC, low_performing_employees DESC, "supervisor_name"
        LIMIT 10
        """

    if "what is the distribution of quality review status across applications" in normalized:
        return f"""
        SELECT
            "application_name",
            "quality_review_status",
            COUNT(*) AS case_count
        FROM {QUERY_TABLE}
        GROUP BY "application_name", "quality_review_status"
        ORDER BY "application_name", "quality_review_status"
        """

    if "identify the top 5 employees with highest audit scores" in normalized:
        return f"""
        WITH employee_scores AS (
            SELECT
                "employee_name",
                "supervisor_name",
                AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name", "supervisor_name"
        ),
        top_employees AS (
            SELECT
                "employee_name",
                "supervisor_name",
                ROUND(average_quality_score, 2) AS average_quality_score
            FROM employee_scores
            ORDER BY average_quality_score DESC, "employee_name"
            LIMIT 5
        )
        SELECT
            t."employee_name",
            t."supervisor_name",
            t.average_quality_score,
            COUNT(*) OVER (PARTITION BY t."supervisor_name") AS top_employee_count_under_supervisor
        FROM top_employees AS t
        ORDER BY t.average_quality_score DESC, t."employee_name"
        """

    if "which table/module has the highest error frequency" in normalized:
        error_expr = _nonperfect_element_count_expr()
        return f"""
        SELECT
            "table_name",
            SUM({error_expr}) AS error_frequency
        FROM {QUERY_TABLE}
        GROUP BY "table_name"
        ORDER BY error_frequency DESC, "table_name"
        LIMIT 1
        """

    if "which root causes are most frequently associated with low scores" in normalized:
        union_sql = _root_recommendation_union(
            extra_condition=f'"quality_score_overall" < {low_score_threshold}'
        )
        return f"""
        WITH root_cause_events AS (
            {union_sql}
        )
        SELECT
            root_cause,
            COUNT(*) AS occurrence_count
        FROM root_cause_events
        WHERE COALESCE(TRIM(root_cause), '') <> ''
        GROUP BY root_cause
        ORDER BY occurrence_count DESC, root_cause
        LIMIT 10
        """

    if "are there specific elements that consistently reduce scores" in normalized:
        union_sql = _element_score_union()
        return f"""
        WITH element_scores AS (
            {union_sql}
        )
        SELECT
            element_name,
            ROUND(AVG(element_score), 2) AS average_element_score
        FROM element_scores
        GROUP BY element_name
        ORDER BY average_element_score ASC, element_name
        LIMIT 10
        """

    if "which application + element combination causes maximum defects" in normalized:
        union_sql = _element_score_union(include_app=True)
        return f"""
        WITH application_element_scores AS (
            {union_sql}
        )
        SELECT
            "application_name",
            element_name,
            COUNT(*) FILTER (WHERE element_score < {DEFAULT_FAIL_THRESHOLD}) AS low_score_count,
            ROUND(AVG(element_score), 2) AS average_element_score
        FROM application_element_scores
        GROUP BY "application_name", element_name
        ORDER BY low_score_count DESC, average_element_score ASC, "application_name", element_name
        LIMIT 10
        """

    if "do certain supervisors have recurring root causes across their team" in normalized:
        union_sql = _root_recommendation_union(include_supervisor=True)
        return f"""
        WITH supervisor_root_causes AS (
            {union_sql}
        )
        SELECT
            "supervisor_name",
            root_cause,
            COUNT(*) AS occurrence_count
        FROM supervisor_root_causes
        WHERE COALESCE(TRIM(root_cause), '') <> ''
        GROUP BY "supervisor_name", root_cause
        ORDER BY occurrence_count DESC, "supervisor_name", root_cause
        LIMIT 15
        """

    if "what are the top 3 recommendations given repeatedly" in normalized:
        recommendation_union = _recommendation_event_union()
        return f"""
        WITH recommendation_events AS (
            {recommendation_union}
        ),
        employee_month_scores AS (
            SELECT
                "employee_name",
                "year",
                "month_audited",
                AVG("quality_score_overall") AS monthly_average_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name", "year", "month_audited"
        ),
        employee_month_transitions AS (
            SELECT
                "employee_name",
                "year",
                "month_audited",
                monthly_average_score AS current_average_score,
                LEAD(monthly_average_score) OVER (
                    PARTITION BY "employee_name"
                    ORDER BY "year", "month_audited"
                ) AS next_average_score
            FROM employee_month_scores
        ),
        top_recommendations AS (
            SELECT
                recommendation,
                COUNT(*) AS occurrence_count
            FROM recommendation_events
            GROUP BY recommendation
            ORDER BY occurrence_count DESC, recommendation
            LIMIT 3
        ),
        sequenced AS (
            SELECT
                r.recommendation,
                t.current_average_score,
                t.next_average_score
            FROM recommendation_events AS r
            INNER JOIN employee_month_transitions AS t
                ON r."employee_name" = t."employee_name"
               AND r."year" = t."year"
               AND r."month_audited" = t."month_audited"
        )
        SELECT
            t.recommendation,
            t.occurrence_count,
            COUNT(*) FILTER (WHERE s.next_average_score IS NOT NULL) AS follow_up_observations,
            ROUND(AVG(s.next_average_score - s.current_average_score), 2) AS average_score_change,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE s.next_average_score IS NOT NULL
                      AND s.next_average_score > s.current_average_score
                ) / NULLIF(COUNT(*) FILTER (WHERE s.next_average_score IS NOT NULL), 0),
                2
            ) AS improvement_rate_percentage
        FROM top_recommendations AS t
        LEFT JOIN sequenced AS s ON t.recommendation = s.recommendation
        GROUP BY t.recommendation, t.occurrence_count
        ORDER BY t.occurrence_count DESC, t.recommendation
        """

    if "which manager has the worst average team performance" in normalized:
        return f"""
        SELECT
            "manager_name",
            ROUND(AVG("quality_score_overall"), 2) AS average_quality_score
        FROM {QUERY_TABLE}
        GROUP BY "manager_name"
        ORDER BY average_quality_score ASC, "manager_name"
        LIMIT 1
        """

    if "drill down: within that manager" in normalized:
        return f"""
        WITH manager_scores AS (
            SELECT "manager_name", AVG("quality_score_overall") AS manager_average_score
            FROM {QUERY_TABLE}
            GROUP BY "manager_name"
        ),
        target_manager AS (
            SELECT "manager_name"
            FROM manager_scores
            ORDER BY manager_average_score ASC, "manager_name"
            LIMIT 1
        ),
        supervisor_scores AS (
            SELECT "supervisor_name", AVG("quality_score_overall") AS supervisor_average_score
            FROM {QUERY_TABLE}
            WHERE "manager_name" = (SELECT "manager_name" FROM target_manager)
            GROUP BY "supervisor_name"
        ),
        target_supervisor AS (
            SELECT "supervisor_name"
            FROM supervisor_scores
            ORDER BY supervisor_average_score ASC, "supervisor_name"
            LIMIT 1
        )
        SELECT
            (SELECT "manager_name" FROM target_manager) AS manager_name,
            (SELECT "supervisor_name" FROM target_supervisor) AS supervisor_name,
            "employee_name",
            ROUND(AVG("quality_score_overall"), 2) AS employee_average_score
        FROM {QUERY_TABLE}
        WHERE "manager_name" = (SELECT "manager_name" FROM target_manager)
          AND "supervisor_name" = (SELECT "supervisor_name" FROM target_supervisor)
        GROUP BY "employee_name"
        ORDER BY employee_average_score ASC, "employee_name"
        LIMIT 1
        """

    if "which director-level hierarchy shows the highest variability in scores" in normalized:
        return f"""
        SELECT
            "director_name",
            ROUND(STDDEV_SAMP("quality_score_overall"), 2) AS score_stddev
        FROM {QUERY_TABLE}
        GROUP BY "director_name"
        ORDER BY score_stddev DESC NULLS LAST, "director_name"
        LIMIT 1
        """

    if "are there managers whose teams show high inconsistency" in normalized:
        return f"""
        SELECT
            "manager_name",
            ROUND(STDDEV_SAMP("quality_score_overall"), 2) AS score_stddev
        FROM {QUERY_TABLE}
        GROUP BY "manager_name"
        ORDER BY score_stddev DESC NULLS LAST, "manager_name"
        LIMIT 10
        """

    if "identify employees who improved over time after repeated recommendations" in normalized:
        return f"""
        SELECT
            "employee_name",
            ROUND(REGR_SLOPE("quality_score_overall", "month_audited"), 4) AS monthly_slope
        FROM {QUERY_TABLE}
        GROUP BY "employee_name"
        HAVING REGR_SLOPE("quality_score_overall", "month_audited") > 0
        ORDER BY monthly_slope DESC, "employee_name"
        LIMIT 20
        """

    if "are audit scores improving month over month per application" in normalized:
        return f"""
        WITH monthly_scores AS (
            SELECT
                "application_name",
                "year",
                "month_audited",
                AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "application_name", "year", "month_audited"
        )
        SELECT
            "application_name",
            "year",
            "month_audited",
            ROUND(average_quality_score, 2) AS average_quality_score,
            ROUND(
                average_quality_score
                - LAG(average_quality_score) OVER (
                    PARTITION BY "application_name"
                    ORDER BY "year", "month_audited"
                ),
                2
            ) AS month_over_month_change
        FROM monthly_scores
        ORDER BY "application_name", "year", "month_audited"
        """

    if "which employees show declining performance trends" in normalized:
        return f"""
        SELECT
            "employee_name",
            ROUND(REGR_SLOPE("quality_score_overall", "month_audited"), 4) AS monthly_slope,
            ROUND(AVG("quality_score_overall"), 2) AS average_quality_score
        FROM {QUERY_TABLE}
        GROUP BY "employee_name"
        HAVING REGR_SLOPE("quality_score_overall", "month_audited") < 0
        ORDER BY monthly_slope ASC, average_quality_score ASC, "employee_name"
        LIMIT 20
        """

    if "do repeated audits on same record id improve quality or not" in normalized:
        return _limitation_sql(
            'This dataset has one row per record_id, so there is no repeated Record ID audit history to measure improvement over time.'
        )

    if "how many cases required multiple reviews before passing" in normalized:
        return _limitation_sql(
            'This dataset does not contain pass/fail workflow history or multiple review events per case, so that metric cannot be calculated reliably.'
        )

    if "is there a learning curve effect per employee" in normalized:
        return f"""
        SELECT
            "employee_name",
            COUNT(*) AS audit_count,
            ROUND(REGR_SLOPE("quality_score_overall", "month_audited"), 4) AS monthly_learning_slope,
            ROUND(MIN("quality_score_overall"), 2) AS lowest_score,
            ROUND(MAX("quality_score_overall"), 2) AS highest_score
        FROM {QUERY_TABLE}
        GROUP BY "employee_name"
        HAVING COUNT(*) >= 5
        ORDER BY monthly_learning_slope DESC, audit_count DESC, "employee_name"
        LIMIT 20
        """

    if "which employees have high failure rate in audits" in normalized:
        return f"""
        SELECT
            "employee_name",
            COUNT(*) AS total_audits,
            SUM(CASE WHEN "quality_score_overall" < {DEFAULT_FAIL_THRESHOLD} THEN 1 ELSE 0 END) AS failed_audits,
            ROUND(
                100.0 * SUM(CASE WHEN "quality_score_overall" < {DEFAULT_FAIL_THRESHOLD} THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS failure_rate_percentage,
            ROUND(AVG("quality_score_overall"), 2) AS average_quality_score
        FROM {QUERY_TABLE}
        GROUP BY "employee_name"
        HAVING COUNT(*) >= 5
        ORDER BY failure_rate_percentage DESC, failed_audits DESC, average_quality_score ASC, "employee_name"
        LIMIT 20
        """

    if "which root causes indicate compliance risk vs minor errors" in normalized:
        risk_topics = [
            "timely_decisions",
            "clinical_accuracy",
            "evidence_based_criteria",
            "patient_safety",
            "regulatory_compliance",
            "safety_indicators",
        ]
        union_parts = []
        for topic in _element_topics():
            severity = "Critical" if topic in risk_topics else "Standard"
            union_parts.append(
                f'SELECT "{QUERY_TABLE}"."root_case_{topic}" AS root_cause, '
                + f'"{QUERY_TABLE}"."element_{topic}" AS element_score, '
                + f'{_sql_literal(severity)} AS severity_group '
                + f'FROM {QUERY_TABLE}'
            )

        return """
        WITH root_events AS (
            {union_sql}
        )
        SELECT
            root_cause,
            SUM(CASE WHEN severity_group = 'Critical' AND element_score < {threshold} THEN 1 ELSE 0 END) AS critical_failure_events,
            SUM(CASE WHEN severity_group = 'Standard' AND element_score < {threshold} THEN 1 ELSE 0 END) AS standard_failure_events,
            CASE
                WHEN SUM(CASE WHEN severity_group = 'Critical' AND element_score < {threshold} THEN 1 ELSE 0 END)
                    >= SUM(CASE WHEN severity_group = 'Standard' AND element_score < {threshold} THEN 1 ELSE 0 END)
                THEN 'Compliance Risk'
                ELSE 'Minor Error Signal'
            END AS risk_classification
        FROM root_events
        WHERE COALESCE(TRIM(root_cause), '') <> ''
        GROUP BY root_cause
        ORDER BY critical_failure_events DESC, standard_failure_events DESC, root_cause
        LIMIT 15
        """.format(union_sql=" UNION ALL ".join(union_parts), threshold=DEFAULT_FAIL_THRESHOLD)

    if "are critical elements being repeatedly missed" in normalized:
        union_parts = []
        for topic in CRITICAL_ELEMENT_TOPICS:
            union_parts.append(
                f'SELECT {_sql_literal(topic)} AS element_name, '
                + f'"element_{topic}" AS element_score '
                + f'FROM {QUERY_TABLE}'
            )
        return f"""
        WITH critical_scores AS (
            {" UNION ALL ".join(union_parts)}
        )
        SELECT
            element_name,
            COUNT(*) AS total_audits,
            COUNT(*) FILTER (WHERE element_score < {DEFAULT_FAIL_THRESHOLD}) AS missed_count,
            ROUND(100.0 * COUNT(*) FILTER (WHERE element_score < {DEFAULT_FAIL_THRESHOLD}) / COUNT(*), 2) AS missed_rate_percentage,
            ROUND(AVG(element_score), 2) AS average_element_score
        FROM critical_scores
        GROUP BY element_name
        ORDER BY missed_rate_percentage DESC, average_element_score ASC, element_name
        """

    if "which teams are risk-prone based on audit failure clusters" in normalized:
        return f"""
        SELECT
            "director_name",
            "manager_name",
            "supervisor_name",
            COUNT(*) AS total_audits,
            SUM(CASE WHEN "quality_score_overall" < {DEFAULT_FAIL_THRESHOLD} THEN 1 ELSE 0 END) AS failed_audits,
            ROUND(
                100.0 * SUM(CASE WHEN "quality_score_overall" < {DEFAULT_FAIL_THRESHOLD} THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS failure_rate_percentage
        FROM {QUERY_TABLE}
        GROUP BY "director_name", "manager_name", "supervisor_name"
        HAVING COUNT(*) >= 20
        ORDER BY failure_rate_percentage DESC, failed_audits DESC, "supervisor_name"
        LIMIT 20
        """

    if "identify outliers in employee performance" in normalized:
        return f"""
        WITH employee_scores AS (
            SELECT
                "employee_name",
                AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name"
        ),
        score_stats AS (
            SELECT
                AVG(average_quality_score) AS company_average_score,
                STDDEV_SAMP(average_quality_score) AS company_score_stddev
            FROM employee_scores
        )
        SELECT
            e."employee_name",
            ROUND(e.average_quality_score, 2) AS average_quality_score,
            ROUND(s.company_average_score, 2) AS company_average_score,
            ROUND(
                (e.average_quality_score - s.company_average_score)
                / NULLIF(s.company_score_stddev, 0),
                2
            ) AS z_score
        FROM employee_scores AS e
        CROSS JOIN score_stats AS s
        WHERE ABS(
            (e.average_quality_score - s.company_average_score)
            / NULLIF(s.company_score_stddev, 0)
        ) >= 2
        ORDER BY z_score ASC, e."employee_name"
        """

    if "does application name influence score more than employee performance" in normalized:
        return f"""
        WITH application_scores AS (
            SELECT "application_name" AS factor_value, AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "application_name"
        ),
        employee_scores AS (
            SELECT "employee_name" AS factor_value, AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name"
        )
        SELECT
            'Application' AS factor,
            ROUND(STDDEV_SAMP(average_quality_score), 2) AS between_group_stddev,
            ROUND(MAX(average_quality_score) - MIN(average_quality_score), 2) AS score_range
        FROM application_scores
        UNION ALL
        SELECT
            'Employee' AS factor,
            ROUND(STDDEV_SAMP(average_quality_score), 2) AS between_group_stddev,
            ROUND(MAX(average_quality_score) - MIN(average_quality_score), 2) AS score_range
        FROM employee_scores
        ORDER BY between_group_stddev DESC, score_range DESC
        """

    if "is performance more dependent on employee, supervisor, or application" in normalized:
        return f"""
        WITH employee_scores AS (
            SELECT 'Employee' AS factor, AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name"
        ),
        supervisor_scores AS (
            SELECT 'Supervisor' AS factor, AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "supervisor_name"
        ),
        application_scores AS (
            SELECT 'Application' AS factor, AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "application_name"
        ),
        factor_scores AS (
            SELECT * FROM employee_scores
            UNION ALL
            SELECT * FROM supervisor_scores
            UNION ALL
            SELECT * FROM application_scores
        )
        SELECT
            factor,
            ROUND(STDDEV_SAMP(average_quality_score), 2) AS between_group_stddev,
            ROUND(MAX(average_quality_score) - MIN(average_quality_score), 2) AS score_range
        FROM factor_scores
        GROUP BY factor
        ORDER BY between_group_stddev DESC, score_range DESC, factor
        """

    if "compare same employee across different applications" in normalized:
        return f"""
        WITH employee_application_scores AS (
            SELECT
                "employee_name",
                "application_name",
                AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name", "application_name"
        ),
        employee_ranges AS (
            SELECT
                "employee_name",
                COUNT(DISTINCT "application_name") AS application_count,
                ROUND(MIN(average_quality_score), 2) AS lowest_application_score,
                ROUND(MAX(average_quality_score), 2) AS highest_application_score,
                ROUND(MAX(average_quality_score) - MIN(average_quality_score), 2) AS score_gap
            FROM employee_application_scores
            GROUP BY "employee_name"
        )
        SELECT
            "employee_name",
            application_count,
            lowest_application_score,
            highest_application_score,
            score_gap
        FROM employee_ranges
        WHERE application_count > 1
        ORDER BY score_gap DESC, "employee_name"
        LIMIT 20
        """

    if "which combination of root cause + element + application gives worst outcomes" in normalized:
        union_sql = _root_recommendation_union(include_app=True)
        return f"""
        WITH defect_events AS (
            {union_sql}
        )
        SELECT
            "application_name",
            element_name,
            root_cause,
            COUNT(*) AS defect_count,
            ROUND(AVG(element_score), 2) AS average_element_score
        FROM defect_events
        WHERE COALESCE(TRIM(root_cause), '') <> ''
        GROUP BY "application_name", element_name, root_cause
        ORDER BY average_element_score ASC, defect_count DESC, "application_name", element_name, root_cause
        LIMIT 15
        """

    if "can we predict low scores using root cause, supervisor, and application" in normalized:
        union_sql = _root_recommendation_union(include_app=True, include_supervisor=True)
        return f"""
        WITH risk_events AS (
            {union_sql}
        )
        SELECT
            "supervisor_name",
            "application_name",
            root_cause,
            COUNT(*) FILTER (WHERE element_score < {DEFAULT_FAIL_THRESHOLD}) AS low_score_event_count,
            ROUND(AVG(element_score), 2) AS average_element_score
        FROM risk_events
        WHERE COALESCE(TRIM(root_cause), '') <> ''
        GROUP BY "supervisor_name", "application_name", root_cause
        HAVING COUNT(*) FILTER (WHERE element_score < {DEFAULT_FAIL_THRESHOLD}) > 0
        ORDER BY low_score_event_count DESC, average_element_score ASC, "supervisor_name", "application_name", root_cause
        LIMIT 20
        """

    if "why is team a under supervisor x consistently underperforming" in normalized:
        return _limitation_sql(
            'This dataset does not have a team field, and "Team A" or "Supervisor X" are placeholders rather than values present in the data.'
        )

    if "are we fixing problems or just documenting them" in normalized:
        recommendation_union = _recommendation_event_union()
        return f"""
        WITH recommendation_events AS (
            {recommendation_union}
        ),
        employee_month_scores AS (
            SELECT
                "employee_name",
                "year",
                "month_audited",
                AVG("quality_score_overall") AS monthly_average_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name", "year", "month_audited"
        ),
        employee_month_transitions AS (
            SELECT
                "employee_name",
                "year",
                "month_audited",
                monthly_average_score AS current_average_score,
                LEAD(monthly_average_score) OVER (
                    PARTITION BY "employee_name"
                    ORDER BY "year", "month_audited"
                ) AS next_average_score
            FROM employee_month_scores
        ),
        sequenced AS (
            SELECT
                r.recommendation,
                t.current_average_score,
                t.next_average_score
            FROM recommendation_events AS r
            INNER JOIN employee_month_transitions AS t
                ON r."employee_name" = t."employee_name"
               AND r."year" = t."year"
               AND r."month_audited" = t."month_audited"
        )
        SELECT
            recommendation,
            COUNT(*) FILTER (WHERE next_average_score IS NOT NULL) AS follow_up_observations,
            COUNT(*) FILTER (
                WHERE next_average_score IS NOT NULL
                  AND next_average_score > current_average_score
            ) AS improved_follow_ups,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE next_average_score IS NOT NULL
                      AND next_average_score > current_average_score
                ) / NULLIF(COUNT(*) FILTER (WHERE next_average_score IS NOT NULL), 0),
                2
            ) AS improvement_rate_percentage
        FROM sequenced
        GROUP BY recommendation
        HAVING COUNT(*) FILTER (WHERE next_average_score IS NOT NULL) > 0
        ORDER BY improvement_rate_percentage DESC, follow_up_observations DESC, recommendation
        """

    if "which recommendation actually works" in normalized:
        recommendation_union = _recommendation_event_union()
        return f"""
        WITH recommendation_events AS (
            {recommendation_union}
        ),
        employee_month_scores AS (
            SELECT
                "employee_name",
                "year",
                "month_audited",
                AVG("quality_score_overall") AS monthly_average_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name", "year", "month_audited"
        ),
        employee_month_transitions AS (
            SELECT
                "employee_name",
                "year",
                "month_audited",
                monthly_average_score AS current_average_score,
                LEAD(monthly_average_score) OVER (
                    PARTITION BY "employee_name"
                    ORDER BY "year", "month_audited"
                ) AS next_average_score
            FROM employee_month_scores
        ),
        sequenced AS (
            SELECT
                r.recommendation,
                t.current_average_score,
                t.next_average_score
            FROM recommendation_events AS r
            INNER JOIN employee_month_transitions AS t
                ON r."employee_name" = t."employee_name"
               AND r."year" = t."year"
               AND r."month_audited" = t."month_audited"
        )
        SELECT
            recommendation,
            COUNT(*) FILTER (WHERE next_average_score IS NOT NULL) AS follow_up_observations,
            ROUND(AVG(next_average_score - current_average_score), 2) AS average_score_change,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE next_average_score IS NOT NULL
                      AND next_average_score > current_average_score
                ) / NULLIF(COUNT(*) FILTER (WHERE next_average_score IS NOT NULL), 0),
                2
            ) AS improvement_rate_percentage
        FROM sequenced
        GROUP BY recommendation
        HAVING COUNT(*) FILTER (WHERE next_average_score IS NOT NULL) > 0
        ORDER BY average_score_change DESC, improvement_rate_percentage DESC, recommendation
        """

    if "if we remove the worst 10% employees, how much does overall quality improve" in normalized:
        return f"""
        WITH employee_scores AS (
            SELECT
                "employee_name",
                AVG("quality_score_overall") AS average_quality_score
            FROM {QUERY_TABLE}
            GROUP BY "employee_name"
        ),
        ranked_employees AS (
            SELECT
                "employee_name",
                average_quality_score,
                NTILE(10) OVER (ORDER BY average_quality_score ASC, "employee_name") AS performance_decile
            FROM employee_scores
        )
        SELECT
            ROUND((SELECT AVG("quality_score_overall") FROM {QUERY_TABLE}), 2) AS current_overall_average,
            ROUND(
                (
                    SELECT AVG(a."quality_score_overall")
                    FROM {QUERY_TABLE} AS a
                    INNER JOIN ranked_employees AS r
                        ON a."employee_name" = r."employee_name"
                    WHERE r.performance_decile > 1
                ),
                2
            ) AS trimmed_overall_average,
            ROUND(
                (
                    SELECT AVG(a."quality_score_overall")
                    FROM {QUERY_TABLE} AS a
                    INNER JOIN ranked_employees AS r
                        ON a."employee_name" = r."employee_name"
                    WHERE r.performance_decile > 1
                ) - (SELECT AVG("quality_score_overall") FROM {QUERY_TABLE}),
                2
            ) AS average_score_improvement
        """

    if "where should we focus training to get maximum impact" in normalized:
        union_sql = _root_recommendation_union()
        return f"""
        WITH training_events AS (
            {union_sql}
        )
        SELECT
            element_name,
            root_cause,
            recommendation,
            COUNT(*) AS occurrence_count,
            ROUND(AVG(element_score), 2) AS average_element_score
        FROM training_events
        WHERE recommendation = 'Training'
           OR root_cause = 'Knowledge'
        GROUP BY element_name, root_cause, recommendation
        ORDER BY occurrence_count DESC, average_element_score ASC, element_name
        LIMIT 15
        """

    return None


def generate_question_bank_sql(question):
    normalized = _normalize_question(question)
    if not normalized:
        return None

    sql = _question_file_one_sql(question, normalized)
    if sql:
        return sql

    return _question_file_two_sql(question, normalized)

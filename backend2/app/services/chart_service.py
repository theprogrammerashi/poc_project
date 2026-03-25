import math


PALETTE = [
    "#E8400C",
    "#00639C",
    "#F7A189",
    "#63B1E5",
    "#008298",
    "#FF6A39",
    "#8EDCE6",
    "#2C2C2C"
]

QUARTER_ORDER = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
TIME_COLUMNS = {
    "audit_month",
    "month_audited",
    "report_month",
    "quarter",
    "report_quarter",
    "year",
}


def _to_records(df):
    records = []
    for row in df.to_dict(orient="records"):
        normalized = {}
        for key, value in row.items():
            if isinstance(value, float) and math.isnan(value):
                normalized[key] = None
            elif hasattr(value, "item"):
                normalized[key] = value.item()
            else:
                normalized[key] = value
        records.append(normalized)
    return records


def _humanize(name):
    clean_name = str(name or "")
    if clean_name.upper() in ["COUNT_STAR()", "COUNT(*)"]:
        return "Failures"
    return clean_name.replace("_", " ").strip().title()


def _is_numeric_dtype(dtype):
    return any(token in str(dtype).lower() for token in ["int", "float", "double", "decimal"])


def _numeric_columns(df):
    return [column for column in df.columns if _is_numeric_dtype(df[column].dtype)]


def _categorical_columns(df):
    return [column for column in df.columns if column not in _numeric_columns(df)]


def _is_time_column(column_name):
    return column_name in TIME_COLUMNS


def _score_like(column_name):
    tokens = ["score", "rate", "percentage", "avg", "average", "stddev", "gap", "change"]
    return any(token in str(column_name).lower() for token in tokens)


def _count_like(column_name):
    tokens = ["count", "total", "volume", "observations", "audits", "cases", "employees"]
    return any(token in str(column_name).lower() for token in tokens)


def _sort_records(records, x_key):
    if not x_key:
        return records

    if x_key in {"quarter", "report_quarter"}:
        return sorted(records, key=lambda row: QUARTER_ORDER.get(str(row.get(x_key)), 99))

    if x_key in {"audit_month", "month_audited", "report_month", "year"}:
        return sorted(records, key=lambda row: (row.get(x_key) is None, row.get(x_key)))

    return records


def _select_x_key(df, categorical_cols):
    time_candidate = next((column for column in df.columns if _is_time_column(column)), None)
    if time_candidate:
        unique_values = df[time_candidate].nunique(dropna=True)
        if unique_values > 1:
            return time_candidate

    non_time_categories = [column for column in categorical_cols if not _is_time_column(column)]
    if non_time_categories:
        return non_time_categories[0]

    if time_candidate:
        return time_candidate

    if categorical_cols:
        return categorical_cols[0]

    return None


def _series(columns):
    result = []
    for index, column in enumerate(columns):
        result.append(
            {
                "key": column,
                "label": _humanize(column),
                "color": PALETTE[index % len(PALETTE)],
            }
        )
    return result


def _base_spec(chart_id, title, rationale, chart_type, data, **extra):
    if isinstance(data, list):
        data_len = len(data)
        if 2 <= data_len <= 4:
            chart_type = "pie"
            extra.pop("layout", None)
            extra.pop("scrollable", None)
        elif 5 <= data_len <= 6:
            chart_type = "bar"
            extra["layout"] = "vertical"
            extra.pop("scrollable", None)
        elif 7 <= data_len <= 10:
            chart_type = "bar"
            extra["layout"] = "horizontal"
        elif data_len > 10:
            chart_type = "area"
            extra.pop("layout", None)
            extra.pop("scrollable", None)
            
    spec = {
        "id": chart_id,
        "title": "Data Visualization",
        "rationale": rationale,
        "type": chart_type,
        "data": data,
    }
    
    if chart_type != "pie":
        orange_shades = ["#E8400C", "#FF6A39", "#F7A189", "#E8400C"]
        for idx, s in enumerate(spec.get("series", [])):
            s["color"] = orange_shades[idx % len(orange_shades)]
            
    spec.update(extra)
    return spec


def _comparison_gap_spec(records, x_key, left_metric, right_metric):
    gap_key = "comparison_gap"
    gap_data = []
    for row in records:
        left_value = row.get(left_metric)
        right_value = row.get(right_metric)
        if left_value is None or right_value is None:
            continue
        gap_row = dict(row)
        gap_row[gap_key] = round(float(left_value) - float(right_value), 2)
        gap_data.append(gap_row)

    if not gap_data:
        return None

    return _base_spec(
        "comparison-gap",
        f"{_humanize(left_metric)} Minus {_humanize(right_metric)}",
        None,
        "line",
        gap_data,
        xKey=x_key,
        series=_series([gap_key]),
    )


def _distribution_share_spec(records, category_key, metric_key):
    if len(records) > 8:
        return None

    return _base_spec(
        "distribution-share",
        f"{_humanize(metric_key)} Share by {_humanize(category_key)}",
        None,
        "pie",
        records,
        xKey=category_key,
        series=_series([metric_key]),
    )


def build_visualizations(df, question=None):
    if df is None or df.empty or len(df) <= 1 or df.shape[1] < 2:
        return []

    if list(df.columns) == ["limitation"]:
        return []

    numeric_cols = _numeric_columns(df)
    categorical_cols = _categorical_columns(df)
    records = _to_records(df)

    if not numeric_cols:
        return []

    x_key = _select_x_key(df, categorical_cols)

    metric_columns = [column for column in numeric_cols if column != x_key]
    if not metric_columns:
        return []

    visuals = []

    if x_key and len(metric_columns) >= 2:
        sorted_records = _sort_records(records, x_key)
        preferred = sorted(
            metric_columns,
            key=lambda column: (
                0 if _score_like(column) else 1,
                0 if _count_like(column) else 1,
                str(column),
            ),
        )

        if _is_time_column(x_key):
            primary_metrics = preferred[: min(2, len(preferred))]
            primary_type = "bar" if len(primary_metrics) > 1 else "area"
            visuals.append(
                _base_spec(
                    "time-comparison",
                    f"{_humanize(x_key)} Comparison",
                    None,
                    primary_type,
                    sorted_records,
                    xKey=x_key,
                    series=_series(primary_metrics),
                )
            )

            remaining_metrics = [column for column in preferred if column not in primary_metrics]
            if remaining_metrics:
                visuals.append(
                    _base_spec(
                        "secondary-trend",
                        f"{_humanize(remaining_metrics[0])} Trend",
                        None,
                        "line",
                        sorted_records,
                        xKey=x_key,
                        series=_series([remaining_metrics[0]]),
                    )
                )
            elif len(primary_metrics) == 2:
                gap_spec = _comparison_gap_spec(
                    sorted_records, x_key, primary_metrics[0], primary_metrics[1]
                )
                if gap_spec:
                    visuals.append(gap_spec)

        elif len(categorical_cols) >= 2:
            series_key = next(column for column in categorical_cols if column != x_key)
            
            combined_key = f"{x_key}_and_{series_key}"
            grouped_rows = []
            for row in sorted_records[:20]:
                new_row = dict(row)
                full_label = f"{row.get(x_key, '')} - {row.get(series_key, '')}".strip(" -")
                # Truncate to prevent SVG label clipping off-screen
                if len(full_label) > 28:
                    full_label = full_label[:25] + "..."
                new_row[combined_key] = full_label
                grouped_rows.append(new_row)
            
            visuals.append(
                _base_spec(
                    "grouped-comparison",
                    f"{_humanize(numeric_cols[0])} by {_humanize(x_key)} and {_humanize(series_key)}",
                    None,
                    "bar",
                    grouped_rows,
                    xKey=combined_key,
                    groupKey=series_key,
                    series=_series([numeric_cols[0]]),
                    layout="horizontal",
                    scrollable=True
                )
            )

            if len(numeric_cols) > 1:
                visuals.append(
                    _base_spec(
                        "secondary-metric",
                        f"{_humanize(numeric_cols[1])} by {_humanize(x_key)}",
                        None,
                        "bar",
                        grouped_rows,
                        xKey=combined_key,
                        groupKey=series_key,
                        series=_series([numeric_cols[1]]),
                        layout="horizontal",
                        scrollable=True
                    )
                )
        else:
            score_metrics = [column for column in preferred if _score_like(column)]
            count_metrics = [column for column in preferred if _count_like(column)]

            if score_metrics and count_metrics:
                visuals.append(
                    _base_spec(
                        "category-volume",
                        f"{_humanize(count_metrics[0])} by {_humanize(x_key)}",
                        None,
                        "bar",
                        sorted_records[:20],
                        xKey=x_key,
                        series=_series([count_metrics[0]]),
                        layout="horizontal",
                    )
                )
                visuals.append(
                    _base_spec(
                        "category-score",
                        f"{_humanize(score_metrics[0])} by {_humanize(x_key)}",
                        None,
                        "bar",
                        sorted_records[:20],
                        xKey=x_key,
                        series=_series([score_metrics[0]]),
                        layout="horizontal",
                    )
                )
                share_spec = _distribution_share_spec(sorted_records[:8], x_key, count_metrics[0])
                if share_spec:
                    visuals.append(share_spec)
            else:
                primary_metrics = preferred[: min(2, len(preferred))]
                visuals.append(
                    _base_spec(
                        "category-comparison",
                        f"{', '.join(_humanize(metric) for metric in primary_metrics)} by {_humanize(x_key)}",
                        None,
                        "bar",
                        sorted_records[:20],
                        xKey=x_key,
                        series=_series(primary_metrics),
                        layout="horizontal",
                    )
                )
                if len(primary_metrics) == 2:
                    gap_spec = _comparison_gap_spec(
                        sorted_records[:20], x_key, primary_metrics[0], primary_metrics[1]
                    )
                    if gap_spec:
                        gap_spec["layout"] = "horizontal"
                        visuals.append(gap_spec)

    elif x_key and len(metric_columns) == 1:
        metric = metric_columns[0]
        sorted_records = _sort_records(records, x_key)

        if _is_time_column(x_key):
            visuals.append(
                _base_spec(
                    "primary-trend",
                    f"{_humanize(metric)} Over {_humanize(x_key)}",
                    None,
                    "area",
                    sorted_records,
                    xKey=x_key,
                    series=_series([metric]),
                )
            )
            visuals.append(
                _base_spec(
                    "time-bars",
                    f"{_humanize(metric)} by {_humanize(x_key)}",
                    None,
                    "bar",
                    sorted_records,
                    xKey=x_key,
                    series=_series([metric]),
                )
            )
        else:
            is_score = _score_like(metric)
            ranked_records = sorted(records, key=lambda row: float(row.get(metric) or 0), reverse=not is_score)[:12]
            visuals.append(
                _base_spec(
                    "ranked-bars",
                    f"{_humanize(metric)} by {_humanize(x_key)}",
                    None,
                    "bar",
                    ranked_records,
                    xKey=x_key,
                    series=_series([metric]),
                    layout="horizontal",
                )
            )
            share_spec = _distribution_share_spec(ranked_records, x_key, metric)
            if share_spec:
                visuals.append(share_spec)

    elif len(metric_columns) >= 2:
        point_data = records[:20]
        visuals.append(
            _base_spec(
                "metric-comparison",
                f"{_humanize(metric_columns[0])} vs {_humanize(metric_columns[1])}",
                None,
                "bar",
                point_data,
                xKey=metric_columns[0],
                series=_series([metric_columns[1]]),
            )
        )

    if question and "distribution" in str(question).lower():
        for v in visuals:
            if isinstance(v.get("data"), list) and len(v.get("data", [])) > 1:
                v["type"] = "pie"
                v.pop("layout", None)
                v.pop("scrollable", None)

    return visuals[:1]


def first_chart_axes(visualizations):
    if not visualizations:
        return None, None, None

    first = visualizations[0]
    series = first.get("series", [])
    first_series_key = series[0]["key"] if series else None
    return first.get("type"), first.get("xKey"), first_series_key


def generate_chart(df, chart_info=None):
    return None

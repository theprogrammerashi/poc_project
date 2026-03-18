import plotly.express as px
import uuid
import os

def generate_chart(df, chart_info=None):

    if df.shape[1] < 2:
        return None

    os.makedirs("charts", exist_ok=True)

    if chart_info:
        chart_type = chart_info.get("chart")
        x = chart_info.get("x")
        y = chart_info.get("y")

        if chart_type == "line":
            fig = px.line(df, x=x, y=y)
        elif chart_type == "pie":
            fig = px.pie(df, names=x, values=y)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x, y=y)
        else:
            fig = px.bar(df, x=x, y=y)
    else:
        # fallback
        x, y = df.columns[0], df.columns[1]
        fig = px.bar(df, x=x, y=y)

    path = f"charts/{uuid.uuid4()}.html"
    fig.write_html(path)

    return path
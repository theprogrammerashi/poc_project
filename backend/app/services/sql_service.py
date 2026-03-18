import re
from app.core.prompts import SQL_PROMPT
from app.db.db import get_connection

def get_schema():
    with get_connection() as con:
        df = con.execute("DESCRIBE audits").df()

    return "\n".join([
        f"{row['column_name']} ({row['column_type']})"
        for _, row in df.iterrows()
    ])

def generate_sql(llm, question, context=None, error=None):
    schema = get_schema()

    system_prompt = SQL_PROMPT + f"\n\nAVAILABLE COLUMNS:\n{schema}"

    if error:
        question = f""" The previous SQL failed with error:
        {error}
        Fix the SQL.
        Original question:
        {question}"""

    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.extend(context)

    messages.append({"role": "user", "content": question})

    sql = llm.generate(messages)

    # Strip markdown code fences if present (```sql ... ```)
    sql = re.sub(r'^```(?:sql)?\s*', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\s*```$', '', sql)
    sql = sql.strip()

    if "select" not in sql.lower():
        raise ValueError(f"Invalid SQL generated: {sql}")

    return sql
import json
import re
from pathlib import Path

from app.db.db import get_connection
from app.services.query_service import _build_exact_answer
from app.services.sql_service import generate_rule_based_sql


DEFAULT_FILE_ONE = Path(r"C:\Users\mruna\Downloads\UM_Clinical_Audit_Questions.txt")
DEFAULT_FILE_TWO = Path(r"C:\Users\mruna\Downloads\audit_questions.txt")


def _parse_first_question_file(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [match.strip() for match in re.findall(r"^\d+\.\s+(.*)$", text, flags=re.MULTILINE)]


def _parse_second_question_file(path):
    text = " ".join(path.read_text(encoding="utf-8", errors="ignore").split())
    numbered = [
        match.strip()
        for match in re.findall(r"\b\d+\.\s+(.*?)(?=\s+\d+\.\s+|\s+BONUS QUESTIONS|$)", text)
    ]

    bonus = []
    bonus_match = re.search(r"BONUS QUESTIONS\s*-\s*(.*)$", text)
    if bonus_match:
        bonus = [
            item.strip()
            for item in re.split(r"\s*-\s*", bonus_match.group(1))
            if item.strip()
        ]

    return numbered + bonus


def _load_questions():
    questions = []
    file_one_questions = _parse_first_question_file(DEFAULT_FILE_ONE)
    file_two_questions = _parse_second_question_file(DEFAULT_FILE_TWO)

    for idx, question in enumerate(file_one_questions, start=1):
        questions.append(
            {
                "source": "UM_Clinical_Audit_Questions.txt",
                "index": idx,
                "question": question,
            }
        )

    for idx, question in enumerate(file_two_questions, start=1):
        questions.append(
            {
                "source": "audit_questions.txt",
                "index": idx,
                "question": question,
            }
        )

    return questions


def _classify_result(df):
    if df is None:
        return "error"
    if list(df.columns) == ["limitation"]:
        return "limitation"
    return "answered"


def evaluate_questions():
    results = []
    questions = _load_questions()

    with get_connection() as con:
        for item in questions:
            question = item["question"]
            sql = generate_rule_based_sql(question)
            if not sql:
                results.append(
                    {
                        **item,
                        "status": "uncovered",
                        "sql": None,
                        "row_count": 0,
                        "columns": [],
                        "preview": [],
                        "chatbot_preview": None,
                    }
                )
                continue

            try:
                df = con.execute(sql).df()
                status = _classify_result(df)
                chatbot_preview = _build_exact_answer(question, df, "")
                preview_rows = df.head(3).to_dict(orient="records")
                results.append(
                    {
                        **item,
                        "status": status,
                        "sql": sql.strip(),
                        "row_count": int(len(df)),
                        "columns": list(df.columns),
                        "preview": preview_rows,
                        "chatbot_preview": chatbot_preview[:600] if chatbot_preview else None,
                    }
                )
            except Exception as error:
                results.append(
                    {
                        **item,
                        "status": "error",
                        "sql": sql.strip(),
                        "row_count": 0,
                        "columns": [],
                        "preview": [],
                        "chatbot_preview": None,
                        "error": str(error),
                    }
                )

    return results


def main():
    results = evaluate_questions()
    counts = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1

    print("QUESTION BANK EVALUATION")
    print(json.dumps(counts, indent=2))
    print()

    misses = [item for item in results if item["status"] in {"uncovered", "error"}]
    if misses:
        print("MISSES")
        for item in misses:
            print(
                f'- [{item["source"]} #{item["index"]}] {item["question"]}'
                + (f' -> {item.get("error")}' if item.get("error") else "")
            )
    else:
        print("No uncovered or error cases.")

    report_path = Path("question_bank_evaluation.json")
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print()
    print(f"Saved detailed report to {report_path.resolve()}")


if __name__ == "__main__":
    main()

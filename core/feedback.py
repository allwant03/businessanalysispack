import csv
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_FILE = Path(__file__).resolve().parent.parent / "feedback.csv"
FIELDNAMES = ["timestamp", "target", "rating", "comment"]


def save(target: str, rating: int, comment: str) -> None:
    is_new = not FEEDBACK_FILE.exists()
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "target": target,
                "rating": rating,
                "comment": comment,
            }
        )


def load_all() -> list[dict]:
    if not FEEDBACK_FILE.exists():
        return []
    with open(FEEDBACK_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_csv_string(rows: list[dict]) -> str:
    if not rows:
        return ""
    from io import StringIO

    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()

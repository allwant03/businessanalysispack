import csv
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

USAGE_FILE = Path(__file__).resolve().parent.parent / "usage_log.csv"
FIELDNAMES = ["timestamp", "target", "tasks_total", "tasks_failed"]


def log_run(target: str, tasks_total: int, tasks_failed: int) -> None:
    is_new = not USAGE_FILE.exists()
    with open(USAGE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "target": target,
                "tasks_total": tasks_total,
                "tasks_failed": tasks_failed,
            }
        )


def load_all() -> list[dict]:
    if not USAGE_FILE.exists():
        return []
    with open(USAGE_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_csv_string(rows: list[dict]) -> str:
    if not rows:
        return ""
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()

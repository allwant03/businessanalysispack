import pandas as pd

# 기업 비교 모드에서는 전체 스키마를 다 돌리면 기업 수만큼 API 호출이 배로 늘어나므로,
# 비교에 실제로 쓰이는 핵심 항목(매출구조/CAPEX/경쟁사 비교=시장점유율 포함)만 돌린다.
COMPARISON_TASK_IDS = {"CO-1", "CO-2", "CP-1"}


def build_comparison_table(compare_results: dict[str, list[dict]]) -> pd.DataFrame:
    """기업별 task_results에서 METRICS를 모아 지표 x 기업 비교표를 만든다.
    METRICS의 label은 보통 "{기업명} 지표명" 형태로 나오므로, 기업명을 떼어내
    같은 지표를 기업 간에 한 행으로 맞춘다(완벽한 매칭은 아니고 best-effort)."""
    best: dict[tuple[str, str], tuple[tuple, str]] = {}

    for company, task_results in compare_results.items():
        for tr in task_results:
            for m in tr["data"].get("metrics", []):
                try:
                    value = float(m.get("value"))
                except (TypeError, ValueError):
                    continue

                label = m.get("label", "") or "지표"
                canon = label.replace(company, "").strip(" ·-:()") or label

                year = m.get("year")
                quarter = m.get("quarter")
                sort_key = (year if isinstance(year, int) else -1, quarter if isinstance(quarter, int) else 0)

                period = m.get("period", "")
                unit = m.get("unit", "")
                value_str = f"{value:g}{unit} ({period})" if period and period != "미상" else f"{value:g}{unit}"

                key = (canon, company)
                if key not in best or sort_key > best[key][0]:
                    best[key] = (sort_key, value_str)

    if not best:
        return pd.DataFrame()

    table: dict[str, dict[str, str]] = {}
    for (canon, company), (_, value_str) in best.items():
        table.setdefault(canon, {})[company] = value_str

    df = pd.DataFrame(table).T
    df.index.name = "지표"
    return df

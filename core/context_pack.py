from .evidence import classify_tier
from .schema import CATEGORY_LABELS

PROMPT_TEMPLATES = [
    ("자소서 · 지원동기", "이 자료와 제 이력서(첨부)를 참고해서, 이 산업에 대한 이해를 바탕으로 지원동기를 작성해줘."),
    ("공모전 · 제품기획", "이 자료와 제가 구상 중인 제품 아이디어(첨부)를 참고해서, 시장 진입 전략과 차별화 포인트를 짚어줘."),
]


def build_pack(target: str, task_results: list[dict]) -> str:
    counters = {"F": 0, "D": 0, "I": 0, "H": 0}
    id_map: dict[tuple[str, str], str] = {}

    def next_id(prefix: str) -> str:
        counters[prefix] += 1
        return f"{prefix}-{counters[prefix]:03d}"

    by_category: dict[str, list[dict]] = {}
    for tr in task_results:
        by_category.setdefault(tr["task"]["category"], []).append(tr)

    lines = [f"# WaferPack Context — {target}", "", f"_반도체 Research Schema 기준, {len(task_results)}개 항목 조사_", ""]

    for category, items in by_category.items():
        lines.append(f"## {CATEGORY_LABELS.get(category, category)}")
        lines.append("")
        for tr in items:
            task, sources, data = tr["task"], tr["sources"], tr["data"]
            lines.append(f"### {task['label']}")
            lines.append("")

            for f in data.get("facts", []):
                gid = next_id("F")
                id_map[(task["id"], f.get("local_id", ""))] = gid
                idx = f.get("source_index")
                src = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else None
                lines.append(f"**[{gid}] FACT**  ")
                lines.append(f.get("statement", ""))
                if src:
                    lines.append(f"Source: {src.get('title', '')} ({src.get('url', '')}) · {classify_tier(src.get('url', ''))}")
                if f.get("reference_date"):
                    lines.append(f"Reference date: {f['reference_date']}")
                lines.append("")

            for d in data.get("discrepancies", []):
                gid = next_id("D")
                lines.append(f"**[{gid}] DISCREPANCY**  ")
                lines.append(d.get("topic", ""))
                for v in d.get("values", []):
                    idx = v.get("source_index")
                    src = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else None
                    label = src.get("title", "출처 미상") if src else "출처 미상"
                    lines.append(f"- {label}: {v.get('value', '')} ({v.get('as_of', '시점 미상')})")
                if d.get("note"):
                    lines.append(f"_{d['note']}_")
                lines.append("")

            for i in data.get("interpretations", []):
                gid = next_id("I")
                based_on = [id_map.get((task["id"], lid), lid) for lid in i.get("based_on_local_ids", [])]
                lines.append(f"**[{gid}] INTERPRETATION**  ")
                lines.append(i.get("statement", ""))
                lines.append(f"Based on: {', '.join(based_on) if based_on else '명시 없음'}")
                lines.append("")

            for h in data.get("hypotheses", []):
                gid = next_id("H")
                lines.append(f"**[{gid}] HYPOTHESIS**  ")
                lines.append(h.get("statement", ""))
                lines.append("")

    lines.append("## 프롬프트 템플릿")
    lines.append("")
    for title, prompt in PROMPT_TEMPLATES:
        lines.append(f"**{title}**  ")
        lines.append(f"> {prompt}")
        lines.append("")

    return "\n".join(lines)

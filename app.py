import concurrent.futures

import pandas as pd
import plotly.express as px
import streamlit as st

from core import config, context_pack, evidence, feedback, llm, schema, search, usage

TIER_COLORS = {"TIER1": "#1f8a5f", "TIER2": "#b8792e", "TIER3": "#7c8990"}


def _render_pie(fig) -> None:
    # 파이차트는 wide 레이아웃 폭에 맞춰 늘리면 원이 작은 채로 옆에 빈 공간만 커져서
    # 정사각형에 가까운 고정 크기로 만들고 가운데 열에 배치한다.
    fig.update_layout(width=420, height=420, margin=dict(t=48, b=10, l=10, r=10))
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.plotly_chart(fig, use_container_width=False)

st.set_page_config(page_title="BusinessAnalysisPack", page_icon="🔬", layout="wide")

st.title("BusinessAnalysisPack")
st.caption("반도체 산업·기업 리서치를 검증된 AI Context Pack으로 만듭니다.")

if not config.is_configured():
    st.warning("`.env` 파일에 ANTHROPIC_API_KEY와 TAVILY_API_KEY를 설정해야 실행할 수 있습니다. `.env.example`을 복사해서 `.env`로 만드세요.")
    st.stop()

MAX_WORKERS = 5


def run_task(task: dict, target: str, retries: int = 1) -> dict:
    try:
        results = search.search(task["query"], time_range=task.get("recency"))
        data = llm.extract(task["label"], target, results)
        return {"task": task, "sources": results, "data": data}
    except Exception:
        if retries > 0:
            return run_task(task, target, retries=retries - 1)
        raise


def _sort_key(item: dict) -> tuple:
    year = item.get("year")
    quarter = item.get("quarter")
    return (year if isinstance(year, int) else -1, quarter if isinstance(quarter, int) else 0)


def render_tier_overview(task_results: list[dict]) -> None:
    counts = {"TIER1": 0, "TIER2": 0, "TIER3": 0}
    for tr in task_results:
        sources = tr["sources"]
        for f in tr["data"].get("facts", []):
            idx = f.get("source_index")
            if isinstance(idx, int) and 0 <= idx < len(sources) and sources[idx].get("url"):
                counts[evidence.classify_tier(sources[idx]["url"])] += 1

    total = sum(counts.values())
    if total == 0:
        return

    df = pd.DataFrame({"Tier": list(counts.keys()), "개수": list(counts.values())})
    fig = px.pie(
        df,
        names="Tier",
        values="개수",
        title=f"출처 신뢰도 분포 (전체 Fact {total}건)",
        color="Tier",
        color_discrete_map=TIER_COLORS,
        hole=0.45,
    )
    _render_pie(fig)


def render_metrics_section(metrics: list[dict], sources: list[dict]) -> None:
    rows = []
    for m in metrics:
        try:
            value = float(m.get("value"))
        except (TypeError, ValueError):
            continue
        idx = m.get("source_index")
        src = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else None
        rows.append(
            {
                "지표": m.get("label", ""),
                "수치": value,
                "단위": m.get("unit", ""),
                "시점": m.get("period", ""),
                "구성그룹": m.get("group") or "",
                "출처": src.get("title", "") if src else "",
                "_sort": _sort_key(m),
            }
        )

    if not rows:
        return

    df = pd.DataFrame(rows)
    st.markdown("**주요 수치**")
    st.dataframe(df[["지표", "수치", "단위", "시점", "출처"]], use_container_width=True, hide_index=True)

    single_df = df[df["구성그룹"] == ""].sort_values("_sort")
    for label, group_df in single_df.groupby("지표", sort=False):
        if group_df["시점"].nunique() >= 2:
            unit = group_df["단위"].iloc[0]
            fig = px.bar(group_df, x="시점", y="수치", title=f"{label} 추이 ({unit})")
            fig.update_xaxes(categoryorder="array", categoryarray=group_df["시점"].tolist())
            fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig, use_container_width=True)

    grouped_df = df[df["구성그룹"] != ""]
    for group_name, group_df in grouped_df.groupby("구성그룹"):
        if len(group_df) >= 2:
            fig = px.pie(group_df, names="지표", values="수치", title=group_name, hole=0.35)
            _render_pie(fig)


def render_discrepancy_table(discrepancies: list[dict], sources: list[dict]) -> None:
    if not discrepancies:
        return
    st.markdown("**⚠️ 자료 간 차이가 있는 부분**")
    for d in discrepancies:
        st.markdown(f"_{d.get('topic', '')}_")
        rows = []
        for v in d.get("values", []):
            idx = v.get("source_index")
            src = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else None
            rows.append(
                {
                    "출처": src.get("title", "출처 미상") if src else "출처 미상",
                    "수치": v.get("value", ""),
                    "시점": v.get("as_of", ""),
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if d.get("note"):
            st.caption(d["note"])


def render_report(target: str, task_results: list[dict]) -> None:
    st.subheader(f"{target} 리포트")
    st.caption("아래 원본 자료(AI Context Pack)를 사람이 읽기 쉽게 정리한 화면입니다. 항목을 눌러 펼쳐보세요.")
    st.caption(
        "**출처 신뢰도** · TIER1: 공시·공공데이터·기업 공식 발표 "
        "· TIER2: 리서치기관·주요 언론 · TIER3: 그 외(블로그, SNS 등 — 별도 확인 권장)"
    )
    render_tier_overview(task_results)

    by_category: dict[str, list[dict]] = {}
    for tr in task_results:
        by_category.setdefault(tr["task"]["category"], []).append(tr)

    for category, items in by_category.items():
        st.markdown(f"#### {schema.CATEGORY_LABELS.get(category, category)}")
        for tr in items:
            task, sources, data = tr["task"], tr["sources"], tr["data"]
            discrepancies = data.get("discrepancies", [])
            interpretations = data.get("interpretations", [])
            facts = data.get("facts", [])
            hypotheses = data.get("hypotheses", [])
            metrics = data.get("metrics", [])

            with st.expander(task["label"]):
                if interpretations:
                    st.markdown("**핵심 해석**")
                    for i in interpretations:
                        st.markdown(f"- {i.get('statement', '')}")

                render_metrics_section(metrics, sources)

                if facts:
                    st.markdown("**세부 근거** (최신순)")
                    sorted_facts = sorted(facts, key=_sort_key, reverse=True)
                    last_year = None
                    for f in sorted_facts:
                        year = f.get("year")
                        if year != last_year:
                            st.markdown(f"###### {year}년" if isinstance(year, int) else "###### 시점 미상")
                            last_year = year
                        st.markdown(f"- {f.get('statement', '')}")
                        idx = f.get("source_index")
                        src = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else None
                        if src and src.get("url"):
                            tier = evidence.classify_tier(src["url"])
                            st.caption(f"[{src.get('title', src['url'])}]({src['url']}) · {tier}")

                if hypotheses:
                    st.markdown("**추정 (직접 근거 없음)**")
                    for h in hypotheses:
                        st.markdown(f"- {h.get('statement', '')}")

                render_discrepancy_table(discrepancies, sources)

                if not (discrepancies or interpretations or facts or hypotheses or metrics):
                    st.caption("이 항목은 조사된 내용이 없습니다.")


target = st.text_input("분석 대상 (기업명 또는 산업명)", placeholder="예: SK하이닉스")
run = st.button("리서치 시작", disabled=not target)

if run:
    tasks = schema.build_tasks(target)
    order = {t["id"]: i for i, t in enumerate(tasks)}
    task_results = []
    failures = []
    progress = st.progress(0.0, text="조사 준비 중...")

    # 클라이언트를 메인 스레드에서 먼저 생성해두면 병렬 실행 시 초기화 경합이 없다.
    search.warmup()
    llm.warmup()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_task, task, target): task for task in tasks}
        done = 0
        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            done += 1
            try:
                task_results.append(future.result())
            except Exception as e:
                failures.append((task["label"], str(e)))
            progress.progress(done / len(tasks), text=f"조사 완료 {done}/{len(tasks)}")

    task_results.sort(key=lambda tr: order[tr["task"]["id"]])

    progress.progress(1.0, text="Context Pack 생성 중...")
    st.session_state["pack_md"] = context_pack.build_pack(target, task_results)
    st.session_state["pack_task_results"] = task_results
    st.session_state["pack_target"] = target
    st.session_state["pack_failures"] = failures
    st.session_state["feedback_done"] = False
    usage.log_run(target, len(tasks), len(failures))
    progress.empty()

if st.session_state.get("pack_failures"):
    for label, err in st.session_state["pack_failures"]:
        st.warning(f"'{label}' 조사 중 오류가 발생해 이 항목은 Context Pack에서 제외됐습니다: {err}")

if "pack_md" in st.session_state:
    render_report(st.session_state["pack_target"], st.session_state["pack_task_results"])

    st.divider()
    st.subheader("AI Context Pack (원본)")
    st.caption(
        "이 파일을 ChatGPT나 Claude에 붙여넣고 원하는 걸 요청하면 됩니다. "
        "예: \"이 자료와 제 이력서를 참고해서 지원동기를 작성해줘\" / "
        "\"이 자료와 제 제품 아이디어를 참고해서 시장 진입 전략을 짚어줘\""
    )
    st.download_button(
        "Context Pack 다운로드 (.md)",
        data=st.session_state["pack_md"],
        file_name=f"businessanalysispack_{st.session_state['pack_target']}.md",
        mime="text/markdown",
    )
    with st.expander("원본 텍스트 보기"):
        st.markdown(st.session_state["pack_md"])

    st.divider()
    st.subheader("이 자료가 도움이 되었나요?")
    if st.session_state.get("feedback_done"):
        st.success("피드백 감사합니다!")
    else:
        rating = st.feedback("stars")
        comment = st.text_area("어떤 부분을 개선하면 좋을까요? (선택)")
        if st.button("피드백 제출", disabled=rating is None):
            feedback.save(
                target=st.session_state["pack_target"],
                rating=rating + 1,
                comment=comment,
            )
            st.session_state["feedback_done"] = True
            st.rerun()

with st.expander("관리자: 사용 현황 · 피드백 보기"):
    code = st.text_input("코드 입력", type="password")
    if code:
        if config.ADMIN_CODE and code == config.ADMIN_CODE:
            usage_rows = usage.load_all()
            st.write(f"**총 사용 횟수: {len(usage_rows)}회**")
            if usage_rows:
                st.dataframe(usage_rows, use_container_width=True)
                st.download_button(
                    "사용 로그 CSV 다운로드",
                    data=usage.to_csv_string(usage_rows),
                    file_name="usage_log.csv",
                    mime="text/csv",
                )

            st.divider()
            rows = feedback.load_all()
            st.write(f"**총 피드백 건수: {len(rows)}건**")
            if rows:
                st.dataframe(rows, use_container_width=True)
                st.download_button(
                    "피드백 CSV 다운로드",
                    data=feedback.to_csv_string(rows),
                    file_name="feedback.csv",
                    mime="text/csv",
                )
        else:
            st.error("코드가 올바르지 않습니다.")

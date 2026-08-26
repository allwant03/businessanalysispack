import concurrent.futures

import streamlit as st

from core import config, context_pack, evidence, feedback, llm, schema, search

st.set_page_config(page_title="BusinessAnalysisPack", page_icon="🔬", layout="wide")

st.title("BusinessAnalysisPack")
st.caption("반도체 산업·기업 리서치를 검증된 AI Context Pack으로 만듭니다.")

if not config.is_configured():
    st.warning("`.env` 파일에 ANTHROPIC_API_KEY와 TAVILY_API_KEY를 설정해야 실행할 수 있습니다. `.env.example`을 복사해서 `.env`로 만드세요.")
    st.stop()

MAX_WORKERS = 5


def run_task(task: dict, target: str) -> dict:
    results = search.search(task["query"])
    data = llm.extract(task["label"], target, results)
    return {"task": task, "sources": results, "data": data}


def render_report(target: str, task_results: list[dict]) -> None:
    st.subheader(f"{target} 리포트")
    st.caption("아래 원본 자료(AI Context Pack)를 사람이 읽기 쉽게 정리한 화면입니다. 항목을 눌러 펼쳐보세요.")

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

            with st.expander(task["label"]):
                if discrepancies:
                    st.markdown("**⚠️ 자료 간 차이가 있는 부분**")
                    for d in discrepancies:
                        st.markdown(f"- {d.get('topic', '')}")
                        if d.get("note"):
                            st.caption(d["note"])

                if interpretations:
                    st.markdown("**핵심 해석**")
                    for i in interpretations:
                        st.markdown(f"- {i.get('statement', '')}")

                if facts:
                    st.markdown("**세부 근거**")
                    for f in facts:
                        st.markdown(f"- {f.get('statement', '')}")
                        idx = f.get("source_index")
                        src = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else None
                        if src:
                            tier = evidence.classify_tier(src.get("url", ""))
                            st.caption(f"{src.get('title', '')} · {tier}")

                if hypotheses:
                    st.markdown("**추정 (직접 근거 없음)**")
                    for h in hypotheses:
                        st.markdown(f"- {h.get('statement', '')}")

                if not (discrepancies or interpretations or facts or hypotheses):
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

with st.expander("관리자: 피드백 보기"):
    code = st.text_input("코드 입력", type="password")
    if code:
        if config.ADMIN_CODE and code == config.ADMIN_CODE:
            rows = feedback.load_all()
            st.write(f"총 {len(rows)}건")
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

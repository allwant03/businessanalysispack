import concurrent.futures

import streamlit as st

from core import config, context_pack, llm, schema, search

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
    st.session_state["pack_target"] = target
    st.session_state["pack_failures"] = failures
    progress.empty()

if st.session_state.get("pack_failures"):
    for label, err in st.session_state["pack_failures"]:
        st.warning(f"'{label}' 조사 중 오류가 발생해 이 항목은 Context Pack에서 제외됐습니다: {err}")

if "pack_md" in st.session_state:
    st.download_button(
        "Context Pack 다운로드 (.md)",
        data=st.session_state["pack_md"],
        file_name=f"businessanalysispack_{st.session_state['pack_target']}.md",
        mime="text/markdown",
    )
    st.divider()
    st.markdown(st.session_state["pack_md"])

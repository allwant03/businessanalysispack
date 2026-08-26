import streamlit as st

from core import config, context_pack, llm, schema, search

st.set_page_config(page_title="WaferPack", page_icon="🔬", layout="wide")

st.title("WaferPack")
st.caption("반도체 산업·기업 리서치를 검증된 AI Context Pack으로 만듭니다.")

if not config.is_configured():
    st.warning("`.env` 파일에 ANTHROPIC_API_KEY와 TAVILY_API_KEY를 설정해야 실행할 수 있습니다. `.env.example`을 복사해서 `.env`로 만드세요.")
    st.stop()

target = st.text_input("분석 대상 (기업명 또는 산업명)", placeholder="예: SK하이닉스")
run = st.button("리서치 시작", disabled=not target)

if run:
    tasks = schema.build_tasks(target)
    task_results = []
    progress = st.progress(0.0, text="조사 준비 중...")

    for idx, task in enumerate(tasks):
        progress.progress(idx / len(tasks), text=f"조사 중 · {task['label']}")
        results = search.search(task["query"])
        data = llm.extract(task["label"], target, results)
        task_results.append({"task": task, "sources": results, "data": data})

    progress.progress(1.0, text="Context Pack 생성 중...")
    st.session_state["pack_md"] = context_pack.build_pack(target, task_results)
    st.session_state["pack_target"] = target
    progress.empty()

if "pack_md" in st.session_state:
    st.download_button(
        "Context Pack 다운로드 (.md)",
        data=st.session_state["pack_md"],
        file_name=f"waferpack_{st.session_state['pack_target']}.md",
        mime="text/markdown",
    )
    st.divider()
    st.markdown(st.session_state["pack_md"])

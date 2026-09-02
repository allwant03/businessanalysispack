import concurrent.futures
import html
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from core import compare, config, context_pack, dart, evidence, feedback, llm, schema, search, usage

TIER_COLORS = {"TIER1": "#1f8a5f", "TIER2": "#b8792e", "TIER3": "#7c8990"}

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', -apple-system, sans-serif; }

h1, h2, h3, h4 { letter-spacing: -0.01em; }

h4 {
    color: #0e7c86;
    border-left: 4px solid #0e7c86;
    padding-left: 10px;
    margin-top: 1.6em !important;
}

.tier-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    padding: 1px 8px;
    border-radius: 4px;
    letter-spacing: 0.03em;
    vertical-align: middle;
}
.tier-badge.tier1 { background: #e0f2e9; color: #1f8a5f; }
.tier-badge.tier2 { background: #f5ead9; color: #b8792e; }
.tier-badge.tier3 { background: #e9edee; color: #7c8990; }

.source-line { font-size: 0.85rem; margin: 2px 0 12px 0; }
.source-line a { color: #5b6b72; text-decoration: none; }
.source-line a:hover { text-decoration: underline; }
</style>
"""


def _source_line(src: dict, tier: str) -> str:
    safe_title = html.escape(src.get("title") or src.get("url", ""))
    safe_url = html.escape(src.get("url", ""), quote=True)
    badge_class = tier.lower()
    return (
        f'<div class="source-line"><a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_title}</a> '
        f'<span class="tier-badge {badge_class}">{tier}</span></div>'
    )


def _render_pie(fig, key: str) -> None:
    # 파이차트는 wide 레이아웃 폭에 맞춰 늘리면 원이 작은 채로 옆에 빈 공간만 커져서
    # 정사각형에 가까운 고정 크기로 만들고 가운데 열에 배치한다.
    fig.update_layout(width=420, height=420, margin=dict(t=48, b=10, l=10, r=10))
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.plotly_chart(fig, use_container_width=False, key=key)


def _render_bar(fig, key: str) -> None:
    # wide 레이아웃 전체 폭(1200px+)에 막대 3~5개짜리 차트를 그냥 늘리면
    # 데이터에 비해 차트만 크고 헐렁해 보인다. 폭을 적당히 제한하고 가운데 배치한다.
    fig.update_layout(width=760, height=380, margin=dict(t=40, b=10, l=10, r=10))
    _, center, _ = st.columns([1, 4, 1])
    with center:
        st.plotly_chart(fig, use_container_width=False, key=key)

st.set_page_config(page_title="BusinessAnalysisPack", page_icon="🔬", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #0e7c86, #0a5f68); padding: 26px 32px;
                border-radius: 10px; margin-bottom: 24px;">
        <div style="color: white; font-size: 1.7rem; font-weight: 700;">BusinessAnalysisPack</div>
        <div style="color: rgba(255,255,255,0.88); font-size: 0.95rem; margin-top: 4px;">
            제조업 산업·기업 리서치를 검증된 AI Context Pack으로 만듭니다.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("공개된 뉴스·공시 기반 일반 리서치용입니다. 진행 중인 내부 프로젝트·협상 정보는 입력하지 마세요.")

if not config.is_configured():
    st.warning("`.env` 파일에 ANTHROPIC_API_KEY와 TAVILY_API_KEY를 설정해야 실행할 수 있습니다. `.env.example`을 복사해서 `.env`로 만드세요.")
    st.stop()

MAX_WORKERS = 5


def run_task(task: dict, target: str, industry: str, retries: int = 1) -> dict:
    try:
        results = search.search(task["query"], time_range=task.get("recency"))
        data = llm.extract(task["label"], target, results, industry=industry)
        return {"task": task, "sources": results, "data": data}
    except Exception:
        if retries > 0:
            return run_task(task, target, industry, retries=retries - 1)
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
    _render_pie(fig, key="tier_overview_pie")


def render_metrics_section(metrics: list[dict], sources: list[dict], key_prefix: str) -> None:
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
    st.markdown("**주요 수치** (최신순)")
    display_df = df.sort_values("_sort", ascending=False)
    st.dataframe(
        display_df[["지표", "수치", "단위", "시점", "출처"]],
        use_container_width=True,
        hide_index=True,
        key=f"{key_prefix}_metrics_df",
    )

    single_df = df[df["구성그룹"] == ""].sort_values("_sort")
    for label, group_df in single_df.groupby("지표", sort=False):
        if group_df["시점"].nunique() >= 2:
            unit = group_df["단위"].iloc[0]
            fig = px.bar(group_df, x="시점", y="수치", title=f"{label} 추이 ({unit})")
            fig.update_xaxes(categoryorder="array", categoryarray=group_df["시점"].tolist())
            _render_bar(fig, key=f"{key_prefix}_bar_{label}")

    grouped_df = df[df["구성그룹"] != ""]
    for group_name, group_df in grouped_df.groupby("구성그룹"):
        if len(group_df) >= 2:
            fig = px.pie(group_df, names="지표", values="수치", title=group_name, hole=0.35)
            _render_pie(fig, key=f"{key_prefix}_pie_{group_name}")


def render_discrepancy_table(discrepancies: list[dict], sources: list[dict], key_prefix: str) -> None:
    if not discrepancies:
        return
    st.markdown("**⚠️ 자료 간 차이가 있는 부분**")
    for idx_d, d in enumerate(discrepancies):
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
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                key=f"{key_prefix}_discrepancy_{idx_d}",
            )
        if d.get("note"):
            st.caption(d["note"])


def render_dart_section(summary: dict) -> None:
    years = sorted(summary["years"].keys(), reverse=True)
    if not years:
        return

    rows = []
    for y in years:
        acc = summary["years"][y]
        revenue = acc.get("매출액")
        op_income = acc.get("영업이익")
        net_income = acc.get("당기순이익")
        liabilities = acc.get("부채총계")
        equity = acc.get("자본총계")
        prev_revenue = summary["years"].get(y - 1, {}).get("매출액")
        yoy = (revenue - prev_revenue) / prev_revenue * 100 if revenue is not None and prev_revenue else None

        rows.append(
            {
                "연도": y,
                "매출액(억원)": round(revenue / 1e8, 1) if revenue is not None else None,
                "영업이익(억원)": round(op_income / 1e8, 1) if op_income is not None else None,
                "당기순이익(억원)": round(net_income / 1e8, 1) if net_income is not None else None,
                "영업이익률(%)": round(op_income / revenue * 100, 1) if revenue and op_income is not None else None,
                "순이익률(%)": round(net_income / revenue * 100, 1) if revenue and net_income is not None else None,
                "부채비율(%)": round(liabilities / equity * 100, 1) if equity else None,
                "매출 YoY(%)": round(yoy, 1) if yoy is not None else None,
            }
        )

    st.subheader("공식 재무제표 (DART)")
    st.caption(f"DART 전자공시시스템 {summary['fs_div']}재무제표 기준 · 수치는 Python이 직접 계산 · TIER1")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, key="dart_summary_df")

    for col, title in [("매출액(억원)", "매출액 추이 (억원)"), ("영업이익(억원)", "영업이익 추이 (억원)")]:
        chart_df = df.dropna(subset=[col]).sort_values("연도")
        if len(chart_df) >= 2:
            fig = px.bar(chart_df, x="연도", y=col, title=title)
            fig.update_xaxes(type="category")
            _render_bar(fig, key=f"dart_{col}")


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
                    st.markdown("**핵심 요약**")
                    st.markdown(" ".join(i.get("statement", "") for i in interpretations))

                render_metrics_section(metrics, sources, key_prefix=task["id"])

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
                            st.markdown(_source_line(src, tier), unsafe_allow_html=True)

                if hypotheses:
                    st.markdown("**추정 (직접 근거 없음)**")
                    for h in hypotheses:
                        st.markdown(f"- {h.get('statement', '')}")

                render_discrepancy_table(discrepancies, sources, key_prefix=task["id"])

                if not (discrepancies or interpretations or facts or hypotheses or metrics):
                    st.caption("이 항목은 조사된 내용이 없습니다.")


with st.sidebar:
    st.markdown("### 분석 설정")
    mode = st.radio("모드", ["단일 기업 분석", "기업 비교", "협력사 발굴"], horizontal=True)
    industry = st.selectbox("업종 선택", options=list(schema.INDUSTRY_SCHEMAS.keys()))

    compare_targets: list[str] = []
    compare_run = False
    discover_run = False
    discover_description = ""

    if mode == "단일 기업 분석":
        target = st.text_input(
            "분석 대상 (기업명 또는 산업명)",
            placeholder=schema.TARGET_PLACEHOLDERS.get(industry, ""),
        )
        include_opportunity = st.checkbox(
            "고객·Pain Point·비즈니스모델까지 조사 (항목 5개 추가, 시간 더 걸림)"
        )
        run = st.button("리서치 시작", disabled=not target, use_container_width=True)
    elif mode == "기업 비교":
        compare_lens = st.radio(
            "비교 관점",
            ["종합 비교", "협력사·파트너 평가"],
            help="종합 비교: 매출구조·CAPEX·경쟁사(점유율) / 협력사·파트너 평가: 재무건전성·가격경쟁력·"
            "생산능력·납기·품질리스크·기존 거래처 — 구매뿐 아니라 영업·전략기획·투자심사에도 씁니다.",
        )
        compare_input = st.text_input(
            "비교할 기업 (쉼표로 구분, 2~3개)",
            placeholder=f"{schema.TARGET_PLACEHOLDERS.get(industry, '')}, ...",
        )
        compare_targets = [t.strip() for t in compare_input.split(",") if t.strip()][:3]
        if compare_lens == "종합 비교":
            st.caption("사업부별 매출 구조 · CAPEX · 경쟁사 비교(시장점유율 포함) 항목만 비교해서 빠르게 확인합니다.")
        else:
            st.caption("재무건전성 · 수익성/원가구조 · 개발능력/기술대응력 · 품질·오너 리스크 · 고객포트폴리오/매출의존도 항목을 비교합니다.")
        compare_run = st.button(
            "비교 시작", disabled=not (2 <= len(compare_targets) <= 3), use_container_width=True
        )
        target = None
        include_opportunity = False
        run = False
    else:  # 협력사 발굴
        discover_description = st.text_input(
            "찾고 있는 부품·기술·서비스",
            placeholder="예: 차량용 배터리프레임 제작, 8인치 파운드리 위탁생산",
        )
        st.caption("이미 아는 회사를 평가하는 게 아니라, 이 부품/기술을 다룰 수 있는 새 후보 기업을 검색으로 찾아줍니다.")
        discover_run = st.button("후보 찾기", disabled=not discover_description, use_container_width=True)
        target = None
        include_opportunity = False
        run = False

if run:
    tasks = schema.build_tasks(target, industry=industry, include_opportunity=include_opportunity)
    order = {t["id"]: i for i, t in enumerate(tasks)}
    task_results = []
    failures = []
    progress = st.progress(0.0, text="조사 준비 중...")

    # 클라이언트를 메인 스레드에서 먼저 생성해두면 병렬 실행 시 초기화 경합이 없다.
    search.warmup()
    llm.warmup()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_task, task, target, industry): task for task in tasks}
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
    st.session_state["pack_md"] = context_pack.build_pack(target, task_results, industry=industry)
    st.session_state["pack_task_results"] = task_results
    st.session_state["pack_target"] = target
    st.session_state["pack_failures"] = failures
    st.session_state["pack_dart"] = dart.get_financial_summary(target, date.today().year)
    st.session_state["feedback_done"] = False
    usage.log_run(target, len(tasks), len(failures))
    progress.empty()

if compare_run:
    search.warmup()
    llm.warmup()
    partner_lens = compare_lens == "협력사·파트너 평가"
    compare_task_ids = compare.PARTNER_TASK_IDS if partner_lens else compare.COMPARISON_TASK_IDS
    company_results: dict[str, list[dict]] = {c: [] for c in compare_targets}
    compare_failures: list[tuple[str, str, str]] = []
    total_tasks = len(compare_targets) * len(compare_task_ids)
    progress = st.progress(0.0, text="비교 조사 준비 중...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for company in compare_targets:
            all_tasks = schema.build_tasks(company, industry=industry, include_partner_eval=partner_lens)
            tasks = [t for t in all_tasks if t["id"] in compare_task_ids]
            for task in tasks:
                futures[executor.submit(run_task, task, company, industry)] = (company, task)

        done = 0
        for future in concurrent.futures.as_completed(futures):
            company, task = futures[future]
            done += 1
            try:
                company_results[company].append(future.result())
            except Exception as e:
                compare_failures.append((company, task["label"], str(e)))
            progress.progress(done / total_tasks, text=f"비교 조사 {done}/{total_tasks}")

    progress.progress(1.0, text="종합 판단 작성 중...")
    verdicts: dict[str, str] = {}
    for company, results in company_results.items():
        task_summaries = [
            {
                "label": tr["task"]["label"],
                "interpretations": tr["data"].get("interpretations", []),
                "facts": tr["data"].get("facts", []),
            }
            for tr in results
        ]
        try:
            verdicts[company] = llm.synthesize_verdict(company, industry, compare_lens, task_summaries)
        except Exception:
            verdicts[company] = ""

    st.session_state["compare_results"] = company_results
    st.session_state["compare_targets"] = compare_targets
    st.session_state["compare_failures"] = compare_failures
    st.session_state["compare_lens"] = compare_lens
    st.session_state["compare_verdicts"] = verdicts
    progress.empty()

if discover_run:
    search.warmup()
    llm.warmup()
    with st.spinner("후보 기업 검색 중..."):
        discover_query = f"{discover_description} 제작 업체 공급 기업"
        discover_results = search.search(discover_query, time_range=None)
        discover_data = llm.discover_suppliers(discover_description, industry, discover_results)
    st.session_state["discover_description"] = discover_description
    st.session_state["discover_data"] = discover_data
    st.session_state["discover_sources"] = discover_results

if st.session_state.get("pack_failures"):
    for label, err in st.session_state["pack_failures"]:
        st.warning(f"'{label}' 조사 중 오류가 발생해 이 항목은 Context Pack에서 제외됐습니다: {err}")

if st.session_state.get("compare_failures"):
    for company, label, err in st.session_state["compare_failures"]:
        st.warning(f"'{company}' - '{label}' 조사 중 오류가 발생해 이 항목은 비교표에서 제외됐습니다: {err}")

if "compare_results" in st.session_state:
    with st.container(border=True):
        targets_label = " vs ".join(st.session_state["compare_targets"])
        lens_label = st.session_state.get("compare_lens", "종합 비교")
        st.subheader(f"{targets_label} 비교 ({lens_label})")
        if lens_label == "협력사·파트너 평가":
            st.caption("재무건전성 · 수익성/원가구조 · 개발능력/기술대응력 · 품질·오너 리스크 · 고객포트폴리오/매출의존도 항목만 돌린 결과입니다. 전체 리포트는 '단일 기업 분석' 모드를 이용하세요.")
            st.warning(
                "⚠️ 공개된 뉴스·재무공시 기반의 **1차 스크리닝 참고용**입니다. 실제 협력사 선정에 필요한 "
                "원가표준 대비 견적 비교, 비상장 협력사 재무 확인, 현장 실사 등 최종 단계 검증은 포함하지 않습니다."
            )
        else:
            st.caption("사업부별 매출 구조 · CAPEX · 경쟁사 비교 항목만 돌린 결과입니다. 전체 리포트는 '단일 기업 분석' 모드를 이용하세요.")

        verdicts = st.session_state.get("compare_verdicts", {})
        if any(verdicts.values()):
            st.markdown("**종합 판단**")
            for company in st.session_state["compare_targets"]:
                v = verdicts.get(company)
                if v:
                    st.markdown(f"**{company}** — {v}")
            st.divider()

        table = compare.build_comparison_table(st.session_state["compare_results"])
        if not table.empty:
            st.markdown("**핵심 수치 비교**")
            st.dataframe(table, use_container_width=True, key="compare_metrics_table")
        else:
            st.caption("비교 가능한 수치가 추출되지 않았습니다.")

        st.markdown("**기업별 요약**")
        cols = st.columns(len(st.session_state["compare_targets"]))
        for col, company in zip(cols, st.session_state["compare_targets"]):
            with col:
                st.markdown(f"**{company}**")
                for tr in st.session_state["compare_results"].get(company, []):
                    interpretations = tr["data"].get("interpretations", [])
                    if interpretations:
                        st.markdown(f"_{tr['task']['label']}_")
                        st.markdown(" ".join(i.get("statement", "") for i in interpretations))

if "discover_data" in st.session_state:
    with st.container(border=True):
        st.subheader(f"'{st.session_state['discover_description']}' 협력사 후보")
        st.caption(
            "검색으로 찾은 후보입니다 — 이미 아는 회사를 평가하는 게 아니라 새 후보를 발굴하는 용도라, "
            "이름이 낯설거나 오탐(관련 없는 기업)이 섞일 수 있습니다. 후보를 추린 뒤에는 '기업 비교' 모드로 넘어가 검증하세요."
        )
        candidates = st.session_state["discover_data"].get("candidates", [])
        sources = st.session_state.get("discover_sources", [])
        if not candidates:
            st.caption("검색 결과에서 뚜렷한 후보 기업을 찾지 못했습니다. 설명을 더 구체적으로 바꿔서 다시 시도해보세요.")
        for c in candidates:
            idx = c.get("source_index")
            src = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else None
            st.markdown(f"**{c.get('name', '')}**")
            st.markdown(c.get("reason", ""))
            if src and src.get("url"):
                tier = evidence.classify_tier(src["url"])
                st.markdown(_source_line(src, tier), unsafe_allow_html=True)

if "pack_md" in st.session_state:
    if st.session_state.get("pack_dart"):
        with st.container(border=True):
            render_dart_section(st.session_state["pack_dart"])

    with st.container(border=True):
        render_report(st.session_state["pack_target"], st.session_state["pack_task_results"])

    with st.container(border=True):
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

    with st.container(border=True):
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
                st.dataframe(usage_rows, use_container_width=True, key="admin_usage_df")
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
                st.dataframe(rows, use_container_width=True, key="admin_feedback_df")
                st.download_button(
                    "피드백 CSV 다운로드",
                    data=feedback.to_csv_string(rows),
                    file_name="feedback.csv",
                    mime="text/csv",
                )
        else:
            st.error("코드가 올바르지 않습니다.")

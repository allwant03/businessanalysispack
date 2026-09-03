"""DART 공시 재무제표만으로 협력사 후보를 정량 스코어링한다.
웹검색·LLM을 전혀 쓰지 않으므로 Gemini/Anthropic API 할당량과 무관하게 동작한다.
코멘토 구매 부트캠프 2차 업무(10개 협력사를 재무제표로 min-max 정규화·가중합해 스코어링)를
그대로 코드로 재현한 것 — 단, DART는 상장사(및 사업보고서 제출대상 대형 비상장사)만 커버한다."""

from . import dart

# (지표, 높을수록 좋은지, 기본 가중치) — 기본은 균등가중(각 25).
FINANCIAL_SCORE_METRICS: list[dict] = [
    {"key": "유동비율", "higher_is_better": True, "default_weight": 25},
    {"key": "부채비율", "higher_is_better": False, "default_weight": 25},
    {"key": "영업이익률", "higher_is_better": True, "default_weight": 25},
    {"key": "순이익률", "higher_is_better": True, "default_weight": 25},
]


def compute_ratios(summary: dict, year: int) -> dict[str, float]:
    """summary는 dart.get_financial_summary()의 반환값. 계정이 없으면 그 비율은 결과에서 빠진다."""
    acc = summary.get("years", {}).get(year, {})
    revenue = acc.get("매출액")
    op_income = acc.get("영업이익")
    net_income = acc.get("당기순이익")
    liabilities = acc.get("부채총계")
    equity = acc.get("자본총계")
    current_assets = acc.get("유동자산")
    current_liabilities = acc.get("유동부채")

    ratios: dict[str, float] = {}
    if current_assets is not None and current_liabilities:
        ratios["유동비율"] = current_assets / current_liabilities * 100
    if liabilities is not None and equity:
        ratios["부채비율"] = liabilities / equity * 100
    if op_income is not None and revenue:
        ratios["영업이익률"] = op_income / revenue * 100
    if net_income is not None and revenue:
        ratios["순이익률"] = net_income / revenue * 100
    return ratios


def _min_max_normalize(values: dict[str, float], higher_is_better: bool) -> dict[str, float]:
    """values: {회사: 원값} -> {회사: 0~100 정규화 점수}. 값이 전부 같으면 중립값 50으로 채운다."""
    vals = list(values.values())
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {k: 50.0 for k in values}
    return {
        k: ((v - lo) / (hi - lo) * 100 if higher_is_better else (hi - v) / (hi - lo) * 100)
        for k, v in values.items()
    }


def score_companies(
    company_ratios: dict[str, dict[str, float]],
    weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """company_ratios: {회사: {지표: 원값}}. weights가 없으면 기본 가중치(각 25) 사용.
    회사마다 확보된 지표 수가 다를 수 있어(공시 누락 등), 실제 반영된 가중치 합으로 나눠 0~100으로 맞춘다."""
    if weights is None:
        weights = {m["key"]: m["default_weight"] for m in FINANCIAL_SCORE_METRICS}
    higher_map = {m["key"]: m["higher_is_better"] for m in FINANCIAL_SCORE_METRICS}

    normalized_by_metric: dict[str, dict[str, float]] = {}
    for metric, w in weights.items():
        if w <= 0:
            continue
        values = {c: r[metric] for c, r in company_ratios.items() if metric in r}
        if len(values) < 2:
            continue
        normalized_by_metric[metric] = _min_max_normalize(values, higher_map[metric])

    scores = {c: 0.0 for c in company_ratios}
    applied_weight = {c: 0.0 for c in company_ratios}
    for metric, norm in normalized_by_metric.items():
        w = weights[metric]
        for c, v in norm.items():
            scores[c] += v * w
            applied_weight[c] += w

    return {c: (scores[c] / applied_weight[c] if applied_weight[c] else 0.0) for c in company_ratios}


def build_score_report(companies: list[str], latest_year: int, weights: dict[str, float] | None = None) -> dict:
    """DART에서 여러 회사의 재무제표를 가져와 비율 계산 + 스코어링까지 한 번에 수행한다.
    반환: {"ratios": {회사: {지표: 값}}, "scores": {회사: 0~100}, "missing": [DART에 없는 회사명]}"""
    company_ratios: dict[str, dict[str, float]] = {}
    missing: list[str] = []

    for company in companies:
        summary = dart.get_financial_summary(company, latest_year)
        if not summary:
            missing.append(company)
            continue
        latest_available_year = max(summary["years"].keys())
        ratios = compute_ratios(summary, latest_available_year)
        if not ratios:
            missing.append(company)
            continue
        company_ratios[company] = ratios

    scores = score_companies(company_ratios, weights) if len(company_ratios) >= 2 else {}
    return {"ratios": company_ratios, "scores": scores, "missing": missing}

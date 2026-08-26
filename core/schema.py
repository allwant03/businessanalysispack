# 반도체 Research Schema — 업종을 바꿀 때는 이 파일만 새로 설계하면 됨 (파이프라인 나머지는 재사용).

# recency: Tavily time_range 힌트. 실적·점유율처럼 최신성이 중요한 항목은 "year"로 제한하고,
# 밸류체인 구조처럼 시간이 지나도 잘 안 바뀌는 항목은 None으로 둬서 좋은 설명 자료가 걸러지지 않게 한다.
SEMICONDUCTOR_SCHEMA = {
    "industry": [
        {
            "id": "IND-1",
            "label": "시장 규모 및 성장률",
            "query": "{target} 반도체 시장 규모 성장률 전망",
            "recency": "year",
        },
        {
            "id": "IND-2",
            "label": "밸류체인 구조 (IDM/Foundry/OSAT)",
            "query": "{target} 반도체 밸류체인 IDM 파운드리 OSAT 구조",
            "recency": None,
        },
        {
            "id": "IND-3",
            "label": "제품군 (메모리/비메모리)",
            "query": "{target} 메모리 반도체 비메모리 HBM DRAM NAND 시장 동향",
            "recency": "year",
        },
        {
            "id": "IND-4",
            "label": "규제 및 무역 이슈",
            "query": "{target} 반도체 수출 규제 관세 이슈",
            "recency": "year",
        },
    ],
    "company": [
        {
            "id": "CO-1",
            "label": "사업부별 매출 구조",
            "query": "{target} 사업부문별 매출 실적",
            "recency": "year",
        },
        {
            "id": "CO-2",
            "label": "설비투자(CAPEX) 계획",
            "query": "{target} CAPEX 설비투자 계획 신규 팹",
            "recency": "year",
        },
        {
            "id": "CO-3",
            "label": "주요 제품 포트폴리오",
            "query": "{target} 주요 제품 라인업",
            "recency": None,
        },
        {
            "id": "CO-4",
            "label": "주요 고객사 구조",
            "query": "{target} 주요 고객사 매출 의존도",
            "recency": "year",
        },
    ],
    "competitor": [
        {
            "id": "CP-1",
            "label": "경쟁사 식별 및 비교",
            "query": "{target} 경쟁사 비교 시장점유율",
            "recency": "year",
        },
        {
            "id": "CP-2",
            "label": "기술/원가 경쟁력",
            "query": "{target} 경쟁사 수율 원가 기술 세대 비교",
            "recency": "year",
        },
    ],
}

# 선택 항목: 산업/기업/경쟁사 분석에서 한 걸음 더 들어가 고객·Pain Point·비즈니스모델까지 조사한다.
# "자소서용"/"공모전용"이라고 목적을 못박지 않고 조사 깊이로만 표현 — 이 자료를 어디에 쓸지는 사용자가 정한다.
OPPORTUNITY_SCHEMA = [
    {
        "id": "OPP-1",
        "label": "고객 세그먼트 및 니즈",
        "query": "{target} 고객사 요구사항 니즈 구매 기준",
        "recency": "year",
    },
    {
        "id": "OPP-2",
        "label": "미충족 수요 및 Pain Point",
        "query": "{target} 산업 문제점 애로사항 개선 요구",
        "recency": "year",
    },
    {
        "id": "OPP-3",
        "label": "유사 제품·서비스 사례",
        "query": "{target} 대체 솔루션 유사 제품 비교",
        "recency": None,
    },
    {
        "id": "OPP-4",
        "label": "비즈니스 모델 사례",
        "query": "{target} 수익모델 비즈니스모델 사례",
        "recency": None,
    },
    {
        "id": "OPP-5",
        "label": "시장 진입 구조 및 진입장벽",
        "query": "{target} 시장 진입장벽 신규진입 규제 라이선스",
        "recency": "year",
    },
]

CATEGORY_LABELS = {
    "industry": "산업",
    "company": "기업",
    "competitor": "경쟁사",
    "opportunity": "사업기회",
}


def build_tasks(target: str, include_opportunity: bool = False) -> list[dict]:
    schema_dict = dict(SEMICONDUCTOR_SCHEMA)
    if include_opportunity:
        schema_dict["opportunity"] = OPPORTUNITY_SCHEMA

    tasks = []
    for category, items in schema_dict.items():
        for item in items:
            tasks.append(
                {
                    "id": item["id"],
                    "category": category,
                    "label": item["label"],
                    "query": item["query"].format(target=target),
                    "recency": item.get("recency"),
                }
            )
    return tasks

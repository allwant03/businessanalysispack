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

CATEGORY_LABELS = {
    "industry": "산업",
    "company": "기업",
    "competitor": "경쟁사",
}


def build_tasks(target: str) -> list[dict]:
    tasks = []
    for category, items in SEMICONDUCTOR_SCHEMA.items():
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

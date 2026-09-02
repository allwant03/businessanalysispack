# 업종별 Research Schema — 업종을 확장할 때는 이 파일에 새 딕셔너리만 추가하면 됨
# (Research Planner 이후 파이프라인 — Evidence Checker, Cross-source Discrepancy Detection,
#  Fact/Interpretation/Hypothesis 분리, 시각화 — 는 전부 그대로 재사용된다).

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
            "query": "{target} 경쟁사 비교 시장점유율 삼성전자 TSMC SK하이닉스 마이크론 UMC PSMC 매그나칩반도체 키파운드리 신카와 한화세미텍 ASMPT Besi",
            "recency": "year",
        },
        {
            "id": "CP-2",
            "label": "기술/원가 경쟁력",
            "query": "{target} 경쟁사 수율 원가 기술 세대 비교 삼성전자 TSMC SK하이닉스 마이크론 UMC PSMC 매그나칩반도체 키파운드리 신카와 한화세미텍 ASMPT Besi",
            "recency": "year",
        },
    ],
}

BATTERY_SCHEMA = {
    "industry": [
        {
            "id": "IND-1",
            "label": "시장 규모 및 성장률",
            "query": "{target} 2차전지 배터리 시장 규모 성장률 전망",
            "recency": "year",
        },
        {
            "id": "IND-2",
            "label": "밸류체인 구조 (소재-셀-팩-완성차)",
            "query": "{target} 배터리 밸류체인 양극재 음극재 분리막 전해액 셀 팩 구조",
            "recency": None,
        },
        {
            "id": "IND-3",
            "label": "배터리 종류 및 기술 동향 (NCM/LFP/전고체)",
            "query": "{target} 배터리 NCM LFP 전고체 기술 동향",
            "recency": "year",
        },
        {
            "id": "IND-4",
            "label": "규제 및 무역 이슈 (IRA/광물)",
            "query": "{target} 배터리 IRA 관세 핵심광물 규제 이슈",
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
            "query": "{target} CAPEX 설비투자 계획 신규 공장 증설",
            "recency": "year",
        },
        {
            "id": "CO-3",
            "label": "주요 제품 포트폴리오",
            "query": "{target} 주요 제품 라인업 배터리 종류",
            "recency": None,
        },
        {
            "id": "CO-4",
            "label": "주요 고객사 구조",
            "query": "{target} 주요 고객사 완성차 매출 의존도",
            "recency": "year",
        },
    ],
    "competitor": [
        {
            "id": "CP-1",
            "label": "경쟁사 식별 및 비교",
            "query": "{target} 경쟁사 비교 시장점유율 LG에너지솔루션 삼성SDI SK온 CATL 에코프로비엠 솔브레인",
            "recency": "year",
        },
        {
            "id": "CP-2",
            "label": "기술/원가 경쟁력",
            "query": "{target} 경쟁사 원가 기술력 비교 LG에너지솔루션 삼성SDI SK온 CATL 에코프로비엠 솔브레인 천보",
            "recency": "year",
        },
    ],
}

AUTO_PARTS_SCHEMA = {
    "industry": [
        {
            "id": "IND-1",
            "label": "시장 규모 및 성장률",
            "query": "{target} 자동차 전장 부품 시장 규모 성장률 전망",
            "recency": "year",
        },
        {
            "id": "IND-2",
            "label": "밸류체인 구조 (완성차/Tier1/Tier2)",
            "query": "{target} 자동차 부품 밸류체인 완성차 OEM Tier1 Tier2 구조",
            "recency": None,
        },
        {
            "id": "IND-3",
            "label": "전장 부품 분류 (파워트레인/ADAS·자율주행/인포테인먼트)",
            "query": "{target} 자동차 전장 파워트레인 ADAS 자율주행 인포테인먼트 기술 동향",
            "recency": "year",
        },
        {
            "id": "IND-4",
            "label": "규제 및 무역 이슈",
            "query": "{target} 자동차 부품 관세 규제 안전 인증 이슈",
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
            "query": "{target} CAPEX 설비투자 계획 신규 공장 증설",
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
            "query": "{target} 주요 고객사 완성차 매출 의존도",
            "recency": "year",
        },
    ],
    "competitor": [
        {
            "id": "CP-1",
            "label": "경쟁사 식별 및 비교",
            "query": "{target} 경쟁사 비교 시장점유율 보쉬 콘티넨탈 덴소 ZF 현대모비스 만도 LG전자 하만",
            "recency": "year",
        },
        {
            "id": "CP-2",
            "label": "기술/원가 경쟁력",
            "query": "{target} 경쟁사 기술 원가 비교 보쉬 콘티넨탈 덴소 ZF 현대모비스 만도 LG전자 하만",
            "recency": "year",
        },
    ],
}

INDUSTRY_SCHEMAS = {
    "반도체": SEMICONDUCTOR_SCHEMA,
    "2차전지": BATTERY_SCHEMA,
    "자동차 전장/부품": AUTO_PARTS_SCHEMA,
}

TARGET_PLACEHOLDERS = {
    "반도체": "예: SK하이닉스",
    "2차전지": "예: LG에너지솔루션",
    "자동차 전장/부품": "예: 현대모비스",
}

# 선택 항목: 산업/기업/경쟁사 분석에서 한 걸음 더 들어가 고객·Pain Point·비즈니스모델까지 조사한다.
# "자소서용"/"공모전용"이라고 목적을 못박지 않고 조사 깊이로만 표현 — 이 자료를 어디에 쓸지는 사용자가 정한다.
# 업종에 상관없이 재사용 가능한 범용 문항이라 업종별로 따로 만들지 않는다.
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

# 선택 항목: 이 회사를 협력사·거래 상대방으로 볼 때의 평가 기준. 실제 완성차 구매팀의 우량 협력사 평가
# 5축(재무제표·수익성/원가효율/개발능력/R&D·품질/리스크신호, 각 20점 100점 만점)을 그대로 반영해서
# 설계했다 — 특히 "개발능력"(수주 프로젝트/차종 수)과 "리스크신호"의 핵심인 "당사의존도"(고객 매출 집중도)는
# 일반적인 기업분석 스키마에는 잘 없는 축이라 명시적으로 넣었다. 구매뿐 아니라 영업(고객사 분석)·
# 전략기획(M&A·제휴 후보 평가)·투자심사·공모전(소싱 파트너 선정)처럼 "이 회사와 거래·제휴할지 판단해야
# 하는" 모든 상황에 쓰일 수 있어 업종에 상관없이 재사용 가능한 범용 문항으로 둔다.
PARTNER_EVALUATION_SCHEMA = [
    {
        "id": "PE-1",
        "label": "재무건전성",
        "query": "{target} 재무건전성 신용등급 부채비율 유동비율 이자보상배율 순이익률",
        "recency": "year",
    },
    {
        "id": "PE-2",
        "label": "수익성 및 원가구조",
        "query": "{target} 영업이익률 수익성 추이 원가구조 원가경쟁력",
        "recency": "year",
    },
    {
        "id": "PE-3",
        "label": "개발능력 및 기술 대응력",
        "query": "{target} 신규 프로젝트 수주 개발능력 R&D 투자 기술 대응력",
        "recency": "year",
    },
    {
        "id": "PE-4",
        "label": "품질 및 거래 리스크",
        "query": "{target} 품질 클레임 불량률 인증 리콜 소송 규제 리스크",
        "recency": "year",
    },
    {
        "id": "PE-5",
        "label": "고객 포트폴리오 및 매출 의존도",
        "query": "{target} 주요 고객사 매출 비중 의존도 거래처 다변화",
        "recency": "year",
    },
]

CATEGORY_LABELS = {
    "industry": "산업",
    "company": "기업",
    "competitor": "경쟁사",
    "opportunity": "사업기회",
    "partner": "협력사 평가",
}


def build_tasks(
    target: str,
    industry: str = "반도체",
    include_opportunity: bool = False,
    include_partner_eval: bool = False,
) -> list[dict]:
    schema_dict = dict(INDUSTRY_SCHEMAS[industry])
    if include_opportunity:
        schema_dict["opportunity"] = OPPORTUNITY_SCHEMA
    if include_partner_eval:
        schema_dict["partner"] = PARTNER_EVALUATION_SCHEMA

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

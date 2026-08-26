# 도메인 기반 신뢰도 등급 — 휴리스틱이므로 실제 사용하며 목록을 계속 보강해야 함.

TIER1_DOMAINS = [
    "dart.fss.or.kr",
    "data.go.kr",
    ".go.kr",
    "sec.gov",  # 미국 상장사(Micron 등) 공시 — DART의 미국판
    # 기업 공식 IR/뉴스룸 — 반도체 스키마 대상 기업 위주, 업종 확장 시 함께 보강
    "news.skhynix.co.kr",
    "skhynix.com",
    "samsung.com",
    "samsungsemiconductor.com",
    "micron.com",
    "tsmc.com",
]

TIER2_DOMAINS = [
    # 업계 리서치/조사기관
    "semi.org",
    "trendforce.com",
    "gartner.com",
    "counterpointresearch.com",
    "idc.com",
    "canalys.com",
    "digitimes.com",
    "wsts.org",
    "coherentmarketinsights.com",
    "researchnester.com",
    "industrialinfo.com",
    "reportprime.com",
    # 재무데이터 애그리게이터 — 원출처가 공시라 블로그보다 신뢰도 높음
    "finance.yahoo.com",
    "macrotrends.net",
    "csimarket.com",
    "tikr.com",
    "kr.investing.com",
    # 통신사·주요 경제지·반도체 전문매체
    "reuters.com",
    "bloomberg.com",
    "yna.co.kr",
    "yonhapnews.co.kr",
    "hankyung.com",
    "mk.co.kr",
    "chosun.com",
    "koreaherald.com",
    "businesskorea.co.kr",
    "etnews.com",
    "thelec.kr",
    "epnc.co.kr",
    "ceoscoredaily.com",
    "edaily.co.kr",
    "sedaily.com",
    "hani.co.kr",
    "joongang.co.kr",
    "news1.kr",
    "zdnet.co.kr",
    "bloter.net",
    "mtn.co.kr",
    "inews24.com",
    "electimes.com",
    "einfomax.co.kr",
    "ajunews.com",
    "nocutnews.co.kr",
]


def classify_tier(url: str) -> str:
    domain = url.split("/")[2].lower() if "//" in url else url.lower()
    if any(d in domain for d in TIER1_DOMAINS):
        return "TIER1"
    if any(d in domain for d in TIER2_DOMAINS):
        return "TIER2"
    return "TIER3"

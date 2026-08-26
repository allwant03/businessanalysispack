import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import requests

from . import config

DART_BASE = "https://opendart.fss.or.kr/api"
CORP_CODE_CACHE = Path(__file__).resolve().parent.parent / ".dart_corp_codes.xml"

# fnlttSinglAcnt(주요계정)의 계정명은 손익 항목에 "(손실)"이 붙는 등 표기가 조금씩 다르므로
# alias로 매핑해서 공통 라벨로 통일한다.
ACCOUNT_ALIASES: dict[str, tuple[str, ...]] = {
    "매출액": ("매출액",),
    "영업이익": ("영업이익",),
    "당기순이익": ("당기순이익(손실)", "당기순이익"),
    "자산총계": ("자산총계",),
    "부채총계": ("부채총계",),
    "자본총계": ("자본총계",),
}


def _canonical_account(name: str) -> str | None:
    for canonical, aliases in ACCOUNT_ALIASES.items():
        if name in aliases:
            return canonical
    return None


def _ensure_corp_codes() -> None:
    if CORP_CODE_CACHE.exists():
        return
    resp = requests.get(f"{DART_BASE}/corpCode.xml", params={"crtfc_key": config.DART_API_KEY}, timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        data = zf.read("CORPCODE.xml")
    CORP_CODE_CACHE.write_bytes(data)


def find_corp_code(company_name: str) -> str | None:
    """상장/공시 기업명 목록에서 corp_code를 찾는다. 해외 기업 등 못 찾으면 None."""
    _ensure_corp_codes()
    root = ET.parse(CORP_CODE_CACHE).getroot()
    name = company_name.strip()
    contains = None
    for el in root.findall("list"):
        corp_name = (el.findtext("corp_name") or "").strip()
        if corp_name == name:
            return el.findtext("corp_code")
        if contains is None and name and name in corp_name and (el.findtext("stock_code") or "").strip():
            contains = el.findtext("corp_code")
    return contains


def _fetch(year: str, corp_code: str, reprt_code: str = "11011") -> list[dict]:
    resp = requests.get(
        f"{DART_BASE}/fnlttSinglAcnt.json",
        params={
            "crtfc_key": config.DART_API_KEY,
            "corp_code": corp_code,
            "bsns_year": year,
            "reprt_code": reprt_code,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "000":
        return []
    return data.get("list", [])


def _to_number(raw) -> float | None:
    try:
        return float(str(raw).replace(",", ""))
    except (TypeError, ValueError):
        return None


def get_financial_summary(company_name: str, latest_year: int) -> dict | None:
    """DART 사업보고서(연간) 기준 최근 3개년 핵심 재무계정을 가져온다.
    fnlttSinglAcnt는 당기/전기/전전기를 한 번의 호출로 함께 주기 때문에 연도별로 따로 부르지 않는다."""
    if not config.DART_API_KEY:
        return None

    corp_code = find_corp_code(company_name)
    if not corp_code:
        return None

    rows: list[dict] = []
    used_year = None
    for offset in range(3):
        year = latest_year - offset
        rows = _fetch(str(year), corp_code)
        if rows:
            used_year = year
            break
    if not rows:
        return None

    fs_div = "CFS" if any(r.get("fs_div") == "CFS" for r in rows) else "OFS"

    years_data: dict[int, dict[str, float]] = {}
    for r in rows:
        if r.get("fs_div") != fs_div:
            continue
        canonical = _canonical_account(r.get("account_nm", ""))
        if canonical is None:
            continue
        for offset, amount_key in ((0, "thstrm_amount"), (1, "frmtrm_amount"), (2, "bfefrmtrm_amount")):
            value = _to_number(r.get(amount_key))
            if value is None:
                continue
            year_accounts = years_data.setdefault(used_year - offset, {})
            year_accounts.setdefault(canonical, value)  # 같은 계정명이 중복되면(예: 지배주주 vs 총계) 먼저 나온 총계 행만 채택

    if not years_data:
        return None

    return {
        "corp_code": corp_code,
        "fs_div": "연결" if fs_div == "CFS" else "별도",
        "years": years_data,
    }

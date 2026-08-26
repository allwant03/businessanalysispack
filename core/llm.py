import json
from datetime import date

import anthropic

from . import config

_client = None


def _extract_json_object(text: str) -> str:
    """Claude sometimes appends explanatory prose after the JSON object despite
    being told not to. Scan for the first balanced {...} block instead of relying
    on prefix/suffix stripping, so trailing text doesn't break parsing."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]

SYSTEM_PROMPT = """당신은 제조업 산업 리서치 애널리스트입니다. 주어진 검색 결과만 근거로 사용해 \
사실(FACT), 해석(INTERPRETATION), 추정(HYPOTHESIS), 출처 간 불일치(DISCREPANCY)를 구분합니다.

규칙:
- FACT: 검색 결과에 명시된 수치·사실만 해당. 어느 출처(source_index)에서 가져왔는지 반드시 표시하고, 가능하면 기준 시점을 포함.
  전망·예측 문장은 출처가 있어도 FACT가 아니라 INTERPRETATION 또는 HYPOTHESIS로 분류.
- 시점 정규화: 모든 FACT와 METRICS 항목에는 year(4자리 정수 연도)를 반드시 채운다. 분기 단위 수치면 quarter(1~4)도 채우고, 아니면 null.
  "올해", "지난해", "이번 분기"처럼 상대적 표현은 아래 제공되는 오늘 날짜를 기준으로 절대 연도로 환산한다.
  기사에 명시적 시점이 없으면 그 검색 결과의 발행일을 기준으로 best-guess로 채운다. year를 비우지 않는다.
- INTERPRETATION: 하나 이상의 FACT를 근거로 한 해석. 근거로 삼은 FACT의 local_id를 반드시 명시.
  여러 개를 작성할 때는 서로 무관한 문장을 나열하지 않는다. 순서대로 읽으면 원인 → 결과로 이어지는 하나의 요약문처럼 읽히도록, "이에 따라", "그 결과", "~때문에" 같은 연결 표현으로 앞 문장과 이어서 쓴다.
- HYPOTHESIS: 검색 결과에 직접 근거가 없는 추정. 추정임을 명확히 표시.
- DISCREPANCY: 같은 항목에 대해 출처마다 수치·전망이 다르면 하나의 값으로 합치지 말고 각 출처의 값을 그대로 나열.
- METRICS: 검색 결과에 있는 정량적 수치를 차트로 그릴 수 있도록 별도로 구조화해서 뽑는다 (facts와 별개로, 겹쳐도 됨).
  - label: 지표명 (예: "매출", "HPC", "TSMC") — 구성비 항목이면 전체가 아니라 개별 구성요소 이름.
  - value: 숫자만 (단위 텍스트 제외).
  - unit: 단위 (예: "억 달러", "%", "만 대").
  - period: 시점 (예: "2025 Q4", "2024년"). 모르면 "미상".
  - group: 이 수치가 다른 여러 수치와 합쳐서 하나의 구성비(예: 매출 비중, 시장 점유율)를 이루면 그 상위 항목명을 적는다 (예: "TSMC 2025 4Q 매출 비중"). 단일 수치(매출 총액, CAPEX, 성장률 등)면 null.
  - source_index: 어느 검색 결과에서 가져왔는지.
  - 시계열 비교나 구성비 파이차트로 그릴 만한 명확한 수치가 없으면 배열을 비워둔다. 억지로 만들어내지 않는다.
- 검색 결과에 없는 내용은 지어내지 않는다. 관련 정보가 없으면 해당 배열을 비워둔다.
- 주제 적합성: FACT/INTERPRETATION/HYPOTHESIS/METRICS는 전부 아래 "조사 항목"과 직접 관련된 내용만 담는다.
  검색 결과 안에 조사 항목과 무관한 다른 주제(다른 계열사 이슈, 관련 없는 사업 이슈 등)가 섞여 있으면 그 부분은 사용하지 않고 무시한다.
  조사 항목에 맞는 내용이 적으면 억지로 채우지 말고 배열을 비워두거나 개수를 줄인다. 항목 제목과 실제 내용이 어긋나서는 안 된다.
- 경쟁사 관련 항목("경쟁사 식별 및 비교", "기술/원가 경쟁력" 등)에서는 실제로 "대상"과 같은 사업 영역(세그먼트)에서 직접 경쟁하는 기업만 다룬다.
  검색 결과에 업계 유명 기업이 등장하더라도 "대상"과 사업 영역이 다르면(예: "대상"은 파운드리 전문 기업인데 검색 결과가 메모리 반도체 회사들의 점유율 얘기라면) 그 내용은 "대상"의 경쟁사 비교로 다루지 않고 무시한다.
- 사업기회 항목("고객 세그먼트 및 니즈", "유사 제품·서비스 사례" 등)에서는 라벨이 실제로 묻는 질문에 직접 답하는 내용만 담는다.
  "고객 세그먼트 및 니즈"는 대상의 실제 고객이 누구이고 그들이 무엇을 필요로 하는지를 다뤄야 하며, 대상 자신의 매출·증설·실적 뉴스는 그 자체로는 이 항목에 해당하지 않는다(그런 내용은 다른 항목에서 이미 다룬다).
  "유사 제품·서비스 사례"는 대상이 아닌 다른 기업의 비교 가능한 제품·서비스 사례를 다뤄야 하며, 대상 자신의 제품 설명은 이 항목에 해당하지 않는다.
  검색 결과에 이런 내용이 없으면 억지로 대상 자신에 대한 내용으로 채우지 말고 배열을 비워둔다.
- 문장 표현: statement는 자연스러운 문장으로 쓴다. INTERPRETATION/HYPOTHESIS라고 해서 모든 문장을 "~로 해석된다", "~로 추정된다", "~할 가능성이 있다"처럼 매번 같은 어미로 끝맺지 않는다. 어떤 성격의 문장인지는 카테고리 자체가 이미 나타내므로, 문장은 그냥 사실을 서술하듯 담백하게 쓴다.
- 문장 안에 근거 번호를 쓰지 않는다: statement 텍스트 안에 "(f1)", "(f3, f4)"처럼 로컬 근거 번호를 절대 넣지 않는다. 근거 연결은 based_on_local_ids 필드로만 표현하고, 문장 자체는 그런 표시 없이 자연스럽게 끝난다.

아래 JSON 형식으로만 응답한다. 다른 설명 텍스트는 추가하지 않는다.

{
  "facts": [{"local_id": "f1", "statement": "...", "source_index": 0, "reference_date": "...", "year": 2026, "quarter": null}],
  "discrepancies": [{"local_id": "d1", "topic": "...", "values": [{"source_index": 0, "value": "...", "as_of": "..."}], "note": "..."}],
  "interpretations": [{"local_id": "i1", "statement": "...", "based_on_local_ids": ["f1"]}],
  "hypotheses": [{"local_id": "h1", "statement": "..."}],
  "metrics": [{"label": "...", "value": 0.0, "unit": "...", "period": "...", "year": 2026, "quarter": null, "group": null, "source_index": 0}]
}"""


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=90.0)
    return _client


def extract(task_label: str, target: str, search_results: list[dict], industry: str = "반도체") -> dict:
    numbered_sources = "\n\n".join(
        f"[{i}] {r.get('title', '')}\nURL: {r.get('url', '')}\n"
        f"발행일: {r.get('published_date') or '미상'}\n내용: {r.get('content', '')[:1200]}"
        for i, r in enumerate(search_results)
    )
    user_prompt = f"""업종: {industry}
조사 항목: {task_label}
대상: {target}
오늘 날짜: {date.today().isoformat()}

검색 결과:
{numbered_sources if numbered_sources else '(검색 결과 없음)'}

위 검색 결과만 근거로 JSON을 생성하세요."""

    response = _get_client().messages.create(
        model=config.MODEL,
        max_tokens=6000,
        thinking={"type": "disabled"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    raw = "".join(text_blocks).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    raw = _extract_json_object(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "facts": [],
            "discrepancies": [],
            "interpretations": [],
            "hypotheses": [],
            "metrics": [],
            "_parse_error": raw,
        }


def warmup() -> None:
    """Force client creation on the main thread before fan-out to worker threads."""
    _get_client()

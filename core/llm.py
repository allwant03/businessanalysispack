import json

import anthropic

from . import config

_client = None

SYSTEM_PROMPT = """당신은 반도체 산업 리서치 애널리스트입니다. 주어진 검색 결과만 근거로 사용해 \
사실(FACT), 해석(INTERPRETATION), 추정(HYPOTHESIS), 출처 간 불일치(DISCREPANCY)를 구분합니다.

규칙:
- FACT: 검색 결과에 명시된 수치·사실만 해당. 어느 출처(source_index)에서 가져왔는지 반드시 표시하고, 가능하면 기준 시점을 포함.
  전망·예측 문장은 출처가 있어도 FACT가 아니라 INTERPRETATION 또는 HYPOTHESIS로 분류.
- INTERPRETATION: 하나 이상의 FACT를 근거로 한 해석. 근거로 삼은 FACT의 local_id를 반드시 명시.
- HYPOTHESIS: 검색 결과에 직접 근거가 없는 추정. 추정임을 명확히 표시.
- DISCREPANCY: 같은 항목에 대해 출처마다 수치·전망이 다르면 하나의 값으로 합치지 말고 각 출처의 값을 그대로 나열.
- 검색 결과에 없는 내용은 지어내지 않는다. 관련 정보가 없으면 해당 배열을 비워둔다.
- 문장 표현: statement는 자연스러운 문장으로 쓴다. INTERPRETATION/HYPOTHESIS라고 해서 모든 문장을 "~로 해석된다", "~로 추정된다", "~할 가능성이 있다"처럼 매번 같은 어미로 끝맺지 않는다. 어떤 성격의 문장인지는 카테고리 자체가 이미 나타내므로, 문장은 그냥 사실을 서술하듯 담백하게 쓴다.

아래 JSON 형식으로만 응답한다. 다른 설명 텍스트는 추가하지 않는다.

{
  "facts": [{"local_id": "f1", "statement": "...", "source_index": 0, "reference_date": "..."}],
  "discrepancies": [{"local_id": "d1", "topic": "...", "values": [{"source_index": 0, "value": "...", "as_of": "..."}], "note": "..."}],
  "interpretations": [{"local_id": "i1", "statement": "...", "based_on_local_ids": ["f1"]}],
  "hypotheses": [{"local_id": "h1", "statement": "..."}]
}"""


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=90.0)
    return _client


def extract(task_label: str, target: str, search_results: list[dict]) -> dict:
    numbered_sources = "\n\n".join(
        f"[{i}] {r.get('title', '')}\nURL: {r.get('url', '')}\n"
        f"발행일: {r.get('published_date') or '미상'}\n내용: {r.get('content', '')[:1200]}"
        for i, r in enumerate(search_results)
    )
    user_prompt = f"""조사 항목: {task_label}
대상: {target}

검색 결과:
{numbered_sources if numbered_sources else '(검색 결과 없음)'}

위 검색 결과만 근거로 JSON을 생성하세요."""

    response = _get_client().messages.create(
        model=config.MODEL,
        max_tokens=4096,
        thinking={"type": "disabled"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    raw = "".join(text_blocks).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"facts": [], "discrepancies": [], "interpretations": [], "hypotheses": [], "_parse_error": raw}


def warmup() -> None:
    """Force client creation on the main thread before fan-out to worker threads."""
    _get_client()

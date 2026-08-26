from tavily import TavilyClient

from . import config

_client = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=config.TAVILY_API_KEY)
    return _client


def _clean_title(title: str, max_len: int = 100) -> str:
    """Some sources (social media posts especially) return their entire body text
    as the 'title' field instead of a real headline. Collapse it to one line and
    cap the length so it doesn't blow up as a giant blob wherever titles are shown."""
    title = " ".join((title or "").split())
    if len(title) > max_len:
        title = title[:max_len].rstrip() + "…"
    return title


def search(query: str, max_results: int = 5, time_range: str | None = None) -> list[dict]:
    kwargs = {"query": query, "max_results": max_results, "search_depth": "advanced"}
    if time_range:
        kwargs["time_range"] = time_range
    response = _get_client().search(**kwargs)
    results = response.get("results", [])
    for r in results:
        r["title"] = _clean_title(r.get("title", ""))
    return results


def warmup() -> None:
    """Force client creation on the main thread before fan-out to worker threads."""
    _get_client()

from tavily import TavilyClient

from . import config

_client = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=config.TAVILY_API_KEY)
    return _client


def search(query: str, max_results: int = 5, time_range: str | None = None) -> list[dict]:
    kwargs = {"query": query, "max_results": max_results, "search_depth": "advanced"}
    if time_range:
        kwargs["time_range"] = time_range
    response = _get_client().search(**kwargs)
    return response.get("results", [])


def warmup() -> None:
    """Force client creation on the main thread before fan-out to worker threads."""
    _get_client()

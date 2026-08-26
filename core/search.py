from tavily import TavilyClient

from . import config

_client = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=config.TAVILY_API_KEY)
    return _client


def search(query: str, max_results: int = 5) -> list[dict]:
    response = _get_client().search(query=query, max_results=max_results, search_depth="advanced")
    return response.get("results", [])

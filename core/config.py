import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL = os.getenv("WAFERPACK_MODEL", "claude-sonnet-5")
ADMIN_CODE = os.getenv("ADMIN_CODE", "")


def is_configured() -> bool:
    return bool(ANTHROPIC_API_KEY and TAVILY_API_KEY)

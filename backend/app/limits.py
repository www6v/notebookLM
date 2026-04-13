"""Role-based resource limits and default LLM configuration."""

ROLE_LIMITS = {
    "free": {
        "max_notebooks": 20,
        "max_sources_per_notebook": 30,
        "max_daily_chats": 50,
        "max_daily_slide_generations": 5,
        "max_daily_deep_research_generations": 3,
    },
    "paid": {
        "max_notebooks": 200,
        "max_sources_per_notebook": 50,
        "max_daily_chats": 200,
        "max_daily_slide_generations": None,
        "max_daily_deep_research_generations": None,
    },
    "admin": {
        "max_notebooks": 200,
        "max_sources_per_notebook": 50,
        "max_daily_chats": 9999,
        "max_daily_slide_generations": None,
        "max_daily_deep_research_generations": None,
    },
}

SUBSCRIPTION_PRICE_MONTHLY = 9900

DEFAULT_LLM_PROVIDER = "dashscope"
DEFAULT_LLM_MODEL = "qwen3.5-plus"

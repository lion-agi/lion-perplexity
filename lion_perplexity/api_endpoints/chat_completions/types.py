from enum import Enum


class SearchRecency(str, Enum):
    """Time interval for search results."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class Model(str, Enum):
    """Available model types."""

    LLAMA_2_70B = "llama-2-70b"
    LLAMA_2_13B = "llama-2-13b"
    LLAMA_3_SMALL = "llama-3.1-sonar-small"
    MIXTRAL_8X7B = "mixtral-8x7b"
    PPLX_7B = "pplx-7b"
    PPLX_70B = "pplx-70b"
    CODE_LLAMA_34B = "codellama-34b"
    CODE_LLAMA_70B = "codellama-70b"


DomainFilter = (
    str  # Domain to whitelist/blacklist (e.g., "example.com" or "-example.com")
)

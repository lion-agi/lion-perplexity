from pydantic import ConfigDict, Field, model_validator

from ....api_endpoints.data_models import PerplexityEndpointRequestBody
from ..types import DomainFilter, SearchRecency
from .message_models import Message


class ChatCompletionRequestBody(PerplexityEndpointRequestBody):
    """Request body for chat completions."""

    model: str = Field(
        description="ID of the model to use. See Model enum for options."
    )

    messages: list[Message] = Field(description="List of messages in the conversation")

    max_tokens: int | None = Field(
        None,
        description=(
            "Maximum number of tokens to generate. If null, will "
            "generate tokens until hitting model's token limit or stop token."
        ),
    )

    temperature: float = Field(
        0.2,
        ge=0,
        lt=2,
        description=(
            "Amount of randomness in the response. Higher values mean more "
            "random, lower values mean more deterministic."
        ),
    )

    top_p: float = Field(
        0.9,
        ge=0,
        le=1,
        description=(
            "Nucleus sampling threshold. Model considers tokens with top_p "
            "probability mass. Lower = less random."
        ),
    )

    return_citations: bool = Field(
        False, description="Whether to return citations with the response"
    )

    search_domain_filter: list[DomainFilter] | None = Field(
        None,
        max_items=3,
        description=(
            "Limit citations to specific domains. Max 3 domains. "
            "Prefix with '-' to blacklist."
        ),
    )

    return_images: bool = Field(
        False, description="Whether to include images in the response"
    )

    return_related_questions: bool = Field(
        False, description="Whether to include related questions"
    )

    search_recency_filter: SearchRecency | None = Field(
        None, description="Time interval for search results"
    )

    top_k: int = Field(
        0,
        ge=0,
        le=2048,
        description=(
            "Number of tokens for top-k filtering. 0 disables filtering. "
            "Don't modify both top_k and top_p."
        ),
    )

    stream: bool = Field(False, description="Whether to stream the response")

    presence_penalty: float = Field(
        0,
        ge=-2.0,
        le=2.0,
        description=(
            "Penalty for new tokens based on presence in text. "
            "Positive values encourage new topics."
        ),
    )

    frequency_penalty: float = Field(
        1,
        gt=0,
        description=(
            "Penalty for token frequency in text. Values > 1.0 discourage "
            "repetition. 1.0 means no penalty."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "llama-3.1-sonar-small",
                "messages": [{"role": "user", "content": "What is Python?"}],
                "temperature": 0.7,
                "return_citations": True,
            }
        }
    )

    @model_validator(mode="after")
    def validate_penalties(self):
        """Validate that only one penalty type is used."""
        if self.presence_penalty != 0 and self.frequency_penalty != 1:
            raise ValueError("Cannot use both presence_penalty and frequency_penalty")
        return self

    @model_validator(mode="after")
    def validate_domain_filters(self):
        """Validate domain filter format."""
        if self.search_domain_filter:
            for domain in self.search_domain_filter:
                if domain.startswith("-"):
                    domain = domain[1:]
                if not domain or "." not in domain:
                    raise ValueError(f"Invalid domain filter: {domain}")
        return self

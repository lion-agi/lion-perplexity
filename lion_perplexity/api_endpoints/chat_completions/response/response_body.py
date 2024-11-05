from typing import Literal

from pydantic import ConfigDict, Field

from ....api_endpoints.data_models import PerplexityEndpointResponseBody
from .choice_models import Choice, ChunkChoice
from .usage_models import Usage


class ChatCompletionResponseBody(PerplexityEndpointResponseBody):
    """Response body for chat completions."""

    id: str = Field(description="Unique identifier for the response")

    model: str = Field(description="Model used for completion")

    object: Literal["chat.completion"] = Field(
        description="Object type, always chat.completion"
    )

    created: int = Field(
        description="Unix timestamp (in seconds) of when the response was created"
    )

    choices: list[Choice] = Field(description="List of completion choices")

    usage: Usage = Field(description="Token usage statistics")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "12345",
                "model": "llama-3.1-sonar-small",
                "object": "chat.completion",
                "created": 1709001234,
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "Python is a programming language.",
                        },
                        "citations": [
                            {
                                "text": "Python is a high-level language",
                                "url": "https://python.org",
                            }
                        ],
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            }
        }
    )


class ChatCompletionChunkResponseBody(PerplexityEndpointResponseBody):
    """Streaming response chunk for chat completions."""

    id: str = Field(description="Unique identifier for the response")

    model: str = Field(description="Model used for completion")

    object: Literal["chat.completion.chunk"] = Field(
        description="Object type, always chat.completion.chunk"
    )

    created: int = Field(description="Unix timestamp (in seconds) of creation")

    choices: list[ChunkChoice] = Field(description="List of chunk choices")

    usage: Usage | None = Field(
        None, description="Token usage statistics (only in final chunk)"
    )

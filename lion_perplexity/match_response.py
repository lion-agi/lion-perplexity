from typing import Any

from .api_endpoints.api_request import PerplexityRequest


def match_response(request_model: PerplexityRequest, response: dict | list) -> Any:
    """Match response to appropriate response model.

    Args:
        request_model: Request model that generated response
        response: Raw response data

    Returns:
        Parsed response object
    """
    endpoint = request_model.endpoint
    method = request_model.method

    if endpoint == "chat/completions":
        if isinstance(response, dict):
            from .api_endpoints.chat_completions.response.response_body import (
                ChatCompletionResponseBody,
            )

            return ChatCompletionResponseBody(**response)
        else:
            # Stream response
            from .api_endpoints.chat_completions.response.response_body import (
                ChatCompletionChunkResponseBody,
            )

            result = []
            for item in response[:-1]:  # Last item is headers
                result.append(ChatCompletionChunkResponseBody(**item))
            return result

    raise ValueError(f"No matching response model for {endpoint} {method}")

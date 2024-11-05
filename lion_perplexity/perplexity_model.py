from typing import Any, AsyncIterator

from lion_service.rate_limiter import RateLimiter, RateLimitError
from pydantic import BaseModel, ConfigDict, Field

from .api_endpoints.api_request import PerplexityRequest
from .api_endpoints.chat_completions.request.request_body import (
    ChatCompletionRequestBody,
)


class PerplexityModel(BaseModel):
    """Model class for handling Perplexity API requests."""

    model: str = Field(description="ID of the model to use")
    request_model: PerplexityRequest = Field(description="Request model for API calls")
    rate_limiter: RateLimiter = Field(description="Rate limiter")
    estimated_output_len: int = Field(
        default=0, description="Expected output length before making request"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        model: str,
        api_key: str,
        endpoint: str,
        method: str,
        content_type: str | None = None,
        limit_tokens: int | None = None,
        limit_requests: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize PerplexityModel."""
        request_model = PerplexityRequest(
            api_key=api_key, endpoint=endpoint, method=method, content_type=content_type
        )

        rate_limiter = RateLimiter(
            limit_tokens=limit_tokens, limit_requests=limit_requests
        )

        super().__init__(
            model=model, request_model=request_model, rate_limiter=rate_limiter
        )

    async def invoke(
        self,
        request_body: ChatCompletionRequestBody | None = None,
        estimated_output_len: int = 0,
        **kwargs: Any,
    ) -> dict | AsyncIterator[dict]:
        """Invoke the model with rate limiting."""
        if request_body and request_body.model != self.model:
            raise ValueError(f"Request model does not match. Model is {self.model}")

        input_token_len = await self.get_input_token_len(request_body)

        if not self.verify_invoke_viability(input_token_len, estimated_output_len):
            raise RateLimitError(
                "Rate limit exceeded",
                input_token_len,
                estimated_output_len or self.estimated_output_len,
            )

        try:
            response, headers = await self.request_model.invoke(
                json_data=request_body, **kwargs
            )

            # Update rate limits based on response
            if response.get("usage"):
                self.rate_limiter.update_rate_limit(
                    headers.get("Date"), response["usage"]["total_tokens"]
                )

            return response

        except Exception as e:
            raise e

    async def stream(
        self, request_body: ChatCompletionRequestBody | None = None, **kwargs: Any
    ) -> AsyncIterator[dict]:
        """Handle streaming responses."""
        if request_body and request_body.model != self.model:
            raise ValueError(f"Request model does not match. Model is {self.model}")

        input_token_len = await self.get_input_token_len(request_body)

        if not self.verify_invoke_viability(input_token_len):
            raise RateLimitError(
                "Rate limit exceeded", input_token_len, self.estimated_output_len
            )

        async for chunk in self.request_model.stream(json_data=request_body, **kwargs):
            yield chunk

    async def get_input_token_len(
        self, request_body: ChatCompletionRequestBody | None
    ) -> int:
        """Get input token length.

        Note: Perplexity doesn't provide token count endpoint yet,
        using character length as approximation.
        """
        if not request_body:
            return 0

        total_chars = 0
        for msg in request_body.messages:
            total_chars += len(msg.content)

        # Rough approximation: 4 characters per token
        return total_chars // 4

    def verify_invoke_viability(
        self, input_tokens_len: int = 0, estimated_output_len: int = 0
    ) -> bool:
        """Verify if invoke is possible with rate limits."""
        self.rate_limiter.release_tokens()

        return self.rate_limiter.check_availability(
            input_tokens_len, estimated_output_len or self.estimated_output_len
        )

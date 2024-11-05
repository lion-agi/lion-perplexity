from typing import Any

from lion_service import Service, register_service

from .api_endpoints.chat_completions.request.request_body import (
    ChatCompletionRequestBody,
)
from .perplexity_model import PerplexityModel


@register_service
class PerplexityService(Service):
    """Service class for Perplexity API."""

    def __init__(
        self,
        api_key: str,
        name: str | None = None,
    ) -> None:
        """Initialize PerplexityService."""
        super().__setattr__("_initialized", False)
        self.api_key = api_key
        self.name = name
        self.rate_limiters = {}  # model: RateLimiter
        super().__setattr__("_initialized", True)

    def __setattr__(self, key: str, value: Any) -> None:
        """Prevent modification of key attributes after initialization."""
        if getattr(self, "_initialized", False) and key in ["api_key"]:
            raise AttributeError(
                f"Cannot modify '{key}' after initialization. "
                f"Please create a new service object."
            )
        super().__setattr__(key, value)

    def create_chat_completion(
        self,
        model: str,
        limit_tokens: int | None = None,
        limit_requests: int | None = None,
    ) -> PerplexityModel:
        """Create a chat completion model instance."""
        model_obj = PerplexityModel(
            model=model,
            api_key=self.api_key,
            endpoint="chat/completions",
            method="POST",
            content_type="application/json",
            limit_tokens=limit_tokens,
            limit_requests=limit_requests,
        )

        return self._check_rate_limiter(
            model_obj, limit_requests=limit_requests, limit_tokens=limit_tokens
        )

    def list_tasks(self) -> list[str]:
        """List available tasks."""
        return ["chat_completion"]

    def match_data_model(self, task_name: str) -> dict:
        """Match task name to data models."""
        if task_name == "chat_completion":
            return {
                "request_body": ChatCompletionRequestBody,
            }
        raise ValueError(f"Unknown task: {task_name}")

    def _check_rate_limiter(
        self,
        model_obj: PerplexityModel,
        limit_requests: int | None = None,
        limit_tokens: int | None = None,
    ) -> PerplexityModel:
        """Check and update rate limiter for the model."""
        if model_obj.model not in self.rate_limiters:
            self.rate_limiters[model_obj.model] = model_obj.rate_limiter
        else:
            model_obj.rate_limiter = self.rate_limiters[model_obj.model]
            if limit_requests:
                model_obj.rate_limiter.limit_requests = limit_requests
            if limit_tokens:
                model_obj.rate_limiter.limit_tokens = limit_tokens

        return model_obj

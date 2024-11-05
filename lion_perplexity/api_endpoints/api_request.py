import json
from typing import Any, AsyncIterator, BinaryIO

import aiohttp
from pydantic import BaseModel


class PerplexityAPIError(Exception):
    """Base exception for Perplexity API errors."""

    def __init__(
        self, message: str, http_status: int | None = None, headers: dict | None = None
    ):
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.headers = headers or {}


class PerplexityRequest:
    """Base class for making requests to Perplexity API."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        method: str,
        content_type: str | None = None,
        base_url: str = "https://api.perplexity.ai",
    ) -> None:
        """Initialize request handler.

        Args:
            api_key: API key for authentication
            endpoint: API endpoint
            method: HTTP method
            content_type: Optional content type
            base_url: Base API URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.endpoint = endpoint
        self.method = method
        self.content_type = content_type
        self.session = None

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self.session is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            if self.content_type:
                headers["Content-Type"] = self.content_type

            self.session = aiohttp.ClientSession(headers=headers)

    def _format_url(self, path_params: dict | None = None) -> str:
        """Format URL with path parameters."""
        endpoint = self.endpoint
        if path_params:
            endpoint = endpoint.format(**path_params)
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    async def invoke(
        self,
        json_data: dict | BaseModel | None = None,
        form_data: dict | None = None,
        params: dict | None = None,
        path_params: dict | None = None,
        output_file: BinaryIO | None = None,
        parse_response: bool = True,
        **kwargs: Any,
    ) -> tuple[dict | bytes | None, dict]:
        """Make request to Perplexity API.

        Args:
            json_data: JSON body data
            form_data: Form data
            params: Query parameters
            path_params: Path parameters
            output_file: Optional file for response
            parse_response: Whether to parse JSON response
            **kwargs: Additional arguments for request

        Returns:
            Tuple of (response data, response headers)

        Raises:
            PerplexityAPIError: On API errors
        """
        await self._ensure_session()

        url = self._format_url(path_params)

        if isinstance(json_data, BaseModel):
            json_data = json_data.model_dump(exclude_unset=True, exclude_none=True)

        try:
            async with self.session.request(
                method=self.method,
                url=url,
                json=json_data,
                data=form_data,
                params=params,
                **kwargs,
            ) as response:
                headers = dict(response.headers)

                if response.status >= 400:
                    error_detail = await response.text()
                    raise PerplexityAPIError(
                        message=f"HTTP {response.status}: {error_detail}",
                        http_status=response.status,
                        headers=headers,
                    )

                if output_file:
                    chunk_size = 8192
                    async for chunk in response.content.iter_chunked(chunk_size):
                        output_file.write(chunk)
                    return None, headers

                if parse_response:
                    return await response.json(), headers
                else:
                    return await response.read(), headers

        except aiohttp.ClientError as e:
            raise PerplexityAPIError(
                message=str(e), http_status=getattr(e, "status", None)
            )

    async def stream(
        self, json_data: dict | BaseModel | None = None, **kwargs: Any
    ) -> AsyncIterator[dict]:
        """Handle streaming responses.

        Args:
            json_data: JSON body data
            **kwargs: Additional arguments

        Yields:
            Streamed response chunks
        """
        await self._ensure_session()

        if isinstance(json_data, BaseModel):
            json_data = json_data.model_dump(exclude_unset=True, exclude_none=True)

        try:
            async with self.session.request(
                method=self.method,
                url=f"{self.base_url}/{self.endpoint.lstrip('/')}",
                json=json_data,
                **kwargs,
            ) as response:
                if response.status >= 400:
                    error_detail = await response.text()
                    raise PerplexityAPIError(
                        message=f"HTTP {response.status}: {error_detail}",
                        http_status=response.status,
                        headers=dict(response.headers),
                    )

                async for line in response.content:
                    if line:
                        if line.startswith(b"data: "):
                            line = line[6:]
                        if line.strip() == b"[DONE]":
                            break
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue

                # Yield headers as last item for rate limiting
                yield dict(response.headers)

        except aiohttp.ClientError as e:
            raise PerplexityAPIError(
                message=str(e), http_status=getattr(e, "status", None)
            )

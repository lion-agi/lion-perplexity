# Copyright (c) 2023 - 2024, HaiyangLi <quantocean.li at gmail dot com>
#
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

import yaml
from lion_service.rate_limiter import RateLimiter, RateLimitError
from lion_service.service_util import invoke_retry
from lion_service.token_calculator import TiktokenCalculator
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from .api_endpoints.api_request import PerplexityRequest
from .api_endpoints.chat_completions.request.request_body import (
    PerplexityChatCompletionRequestBody,
)
from .api_endpoints.match_response import match_response

path = Path(__file__).parent

price_config_file_name = path / "perplexity_price_data.yaml"
max_output_token_file_name = path / "perplexity_max_output_token_data.yaml"


class PerplexityModel(BaseModel):
    model: str = Field(description="ID of the model to use.")

    request_model: PerplexityRequest = Field(description="Making requests")

    rate_limiter: RateLimiter = Field(
        description="Rate Limiter to track usage"
    )

    text_token_calculator: TiktokenCalculator = Field(
        default=None, description="Token Calculator"
    )

    estimated_output_len: int = Field(
        default=0, description="Expected output len before making request"
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def parse_input(cls, data: dict):
        if not isinstance(data, dict):
            raise ValueError("Invalid init param")

        # parse request model
        request_model_params = {
            "api_key": data.pop("api_key", None),
            "endpoint": data.pop("endpoint", None),
            "method": data.pop("method", None),
            "content_type": data.pop("content_type", None),
        }
        try:
            api_key = os.getenv(request_model_params["api_key"], None)
            if api_key:
                request_model_params["api_key"] = api_key
        except Exception:
            pass

        data["request_model"] = PerplexityRequest(**request_model_params)

        # parse rate limiter
        if "rate_limiter" not in data:
            rate_limiter_params = {}
            if limit_tokens := data.pop("limit_tokens", None):
                rate_limiter_params["limit_tokens"] = limit_tokens
            if limit_requests := data.pop("limit_requests", None):
                rate_limiter_params["limit_requests"] = limit_requests

            data["rate_limiter"] = RateLimiter(**rate_limiter_params)

        # parse token calculator
        try:
            # Perplexity uses cl100k_base encoding like OpenAI
            text_calc = TiktokenCalculator(encoding_name="cl100k_base")
            data["text_token_calculator"] = text_calc
        except Exception:
            pass

        return data

    @field_serializer("request_model")
    def serialize_request_model(self, value: PerplexityRequest):
        return value.model_dump(exclude_unset=True)

    @invoke_retry(max_retries=3, base_delay=1, max_delay=60)
    async def invoke(
        self,
        request_body: PerplexityChatCompletionRequestBody,
        estimated_output_len: int = 0,
        output_file=None,
        parse_response=True,
    ):
        if request_model := getattr(request_body, "model"):
            if request_model != self.model:
                raise ValueError(
                    f"Request model does not match. Model is {self.model}, but request is made for {request_model}."
                )

        # check remaining rate limit
        input_token_len = await self.get_input_token_len(request_body)

        if getattr(request_body, "max_tokens", None):
            estimated_output_len = request_body.max_tokens

        invoke_viability_result = self.verify_invoke_viability(
            input_tokens_len=input_token_len,
            estimated_output_len=estimated_output_len,
        )
        if not invoke_viability_result:
            raise RateLimitError(
                message="Rate limit reached for requests",
                input_token_len=input_token_len,
                estimated_output_len=estimated_output_len,
            )

        try:
            if getattr(request_body, "stream", None):
                return await self.stream(
                    request_body,
                    output_file=output_file,
                    parse_response=parse_response,
                )

            response_body, response_headers = await self.request_model.invoke(
                json_data=request_body,
                output_file=output_file,
                with_response_header=True,
                parse_response=False,
            )

            if response_body:
                # Update rate limit based on usage
                if response_body.get("usage"):
                    total_token_usage = response_body["usage"]["total_tokens"]
                    if date_str := response_headers.get("date"):
                        self.rate_limiter.update_rate_limit(
                            date_str, total_token_usage
                        )
                    else:
                        self.rate_limiter.update_rate_limit(
                            None, total_token_usage
                        )
                else:
                    self.rate_limiter.update_rate_limit(None)

            if parse_response:
                return match_response(self.request_model, response_body)
            else:
                return response_body

        except Exception as e:
            raise e

    async def stream(
        self,
        request_body: PerplexityChatCompletionRequestBody,
        output_file=None,
        parse_response=True,
        verbose=True,
    ):
        response_chunks = []
        response_headers = None

        async for chunk in self.request_model.stream(
            json_data=request_body,
            output_file=output_file,
            with_response_header=True,
            verbose=verbose,
        ):
            if isinstance(chunk, dict):
                if "headers" in chunk:
                    response_headers = chunk["headers"]
                else:
                    response_chunks.append(chunk)

        # Update rate limit if we have usage information
        if response_chunks and response_chunks[-1].get("usage"):
            total_token_usage = response_chunks[-1]["usage"]["total_tokens"]
            if date_str := response_headers.get("date"):
                self.rate_limiter.update_rate_limit(
                    date_str, total_token_usage
                )
            else:
                self.rate_limiter.update_rate_limit(None, total_token_usage)

        if parse_response:
            return match_response(self.request_model, response_chunks)
        else:
            return response_chunks

    async def get_input_token_len(
        self, request_body: PerplexityChatCompletionRequestBody
    ):
        if request_model := getattr(request_body, "model"):
            if request_model != self.model:
                raise ValueError(
                    f"Request model does not match. Model is {self.model}, but request is made for {request_model}."
                )

        total_tokens = 0
        for message in request_body.messages:
            total_tokens += self.text_token_calculator.calculate(
                message.content
            )

        return total_tokens

    def verify_invoke_viability(
        self, input_tokens_len: int = 0, estimated_output_len: int = 0
    ):
        self.rate_limiter.release_tokens()

        estimated_output_len = (
            estimated_output_len
            if estimated_output_len != 0
            else self.estimated_output_len
        )
        if estimated_output_len == 0:
            with open(max_output_token_file_name) as file:
                output_token_config = yaml.safe_load(file)
                estimated_output_len = output_token_config.get(self.model, 0)
                self.estimated_output_len = estimated_output_len

        if self.rate_limiter.check_availability(
            input_tokens_len, estimated_output_len
        ):
            return True
        else:
            return False

    def estimate_text_price(
        self,
        input_text: str,
        estimated_num_of_output_tokens: int = 0,
    ):
        if self.text_token_calculator is None:
            raise ValueError("Token calculator not available")

        num_of_input_tokens = self.text_token_calculator.calculate(input_text)

        with open(price_config_file_name) as file:
            price_config = yaml.safe_load(file)

        model_price_info_dict = price_config["model"][self.model]
        estimated_price = (
            model_price_info_dict["input_tokens"] * num_of_input_tokens
            + model_price_info_dict["output_tokens"]
            * estimated_num_of_output_tokens
        )

        return estimated_price

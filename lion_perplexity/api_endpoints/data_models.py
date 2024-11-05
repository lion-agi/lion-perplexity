from pydantic import BaseModel, ConfigDict


class PerplexityEndpointRequestBody(BaseModel):
    """Base class for Perplexity API request bodies."""

    model_config = ConfigDict(
        extra="forbid", use_enum_values=True, validate_assignment=True
    )


class PerplexityEndpointResponseBody(BaseModel):
    """Base class for Perplexity API response bodies."""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)


class PerplexityEndpointQueryParam(BaseModel):
    """Base class for query parameters."""

    model_config = ConfigDict(
        extra="forbid", use_enum_values=True, validate_assignment=True
    )


class PerplexityEndpointPathParam(BaseModel):
    """Base class for path parameters."""

    model_config = ConfigDict(
        extra="forbid", use_enum_values=True, validate_assignment=True
    )

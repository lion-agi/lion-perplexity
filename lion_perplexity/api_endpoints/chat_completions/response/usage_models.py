from pydantic import BaseModel, ConfigDict, Field


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(description="Number of tokens in the prompt")
    completion_tokens: int = Field(description="Number of tokens in the completion")
    total_tokens: int = Field(description="Total tokens used in the request")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            }
        }
    )

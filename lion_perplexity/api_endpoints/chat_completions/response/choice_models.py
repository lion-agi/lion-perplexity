from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from ..request.message_models import Message


class FinishReason(str, Enum):
    """Reason why the model stopped generating tokens."""

    STOP = "stop"
    LENGTH = "length"
    MAX_TOKENS = "max_tokens"
    CANCELLED = "cancelled"


class Citation(BaseModel):
    """Citation for a source used in response."""

    text: str = Field(description="Cited text snippet")
    url: str = Field(description="Source URL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Python is a high-level programming language",
                "url": "https://example.com/python",
            }
        }
    )


class RelatedQuestion(BaseModel):
    """Related question suggestion."""

    question: str = Field(description="Related question text")

    model_config = ConfigDict(
        json_schema_extra={"example": {"question": "What are Python's main features?"}}
    )


class ImageReference(BaseModel):
    """Image returned in response."""

    url: str = Field(description="Image URL")
    title: str | None = Field(None, description="Image title if available")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"url": "https://example.com/image.jpg", "title": "Python Logo"}
        }
    )


class Choice(BaseModel):
    """A completion choice from the model."""

    index: int = Field(description="Index of this choice")
    finish_reason: FinishReason = Field(
        description="Reason the model stopped generating"
    )
    message: Message = Field(description="The generated message")
    citations: List[Citation] | None = Field(
        None, description="Sources cited in the response"
    )
    related_questions: List[RelatedQuestion] | None = Field(
        None, description="Related questions suggested"
    )
    images: List[ImageReference] | None = Field(
        None, description="Images included in response"
    )

    model_config = ConfigDict(use_enum_values=True)


class ChunkChoice(BaseModel):
    """A streaming response chunk choice."""

    index: int = Field(description="Index of this choice")
    finish_reason: FinishReason | None = Field(
        None, description="Reason for finishing, if finished"
    )
    delta: Message = Field(description="Incremental content update")

    model_config = ConfigDict(use_enum_values=True)

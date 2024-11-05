from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    """Role in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Message in a chat conversation."""

    role: Role = Field(description="Role of the message author")
    content: str = Field(description="Content of the message")
    name: str | None = Field(
        None, description="Identifier for the author of this message"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {"role": "user", "content": "What is Python?", "name": None}
        },
    )

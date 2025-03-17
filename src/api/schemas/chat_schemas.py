from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator, Field
from fastapi import HTTPException


class CreateChatOutputSchema(BaseModel):
    """
    Represents the output schema for the 'create_new_chat' endpoint.

    Attributes:
        chat_id (str): The new chat's ID (a UUID).
    """
    chat_id: str


class ChatOutputSchema(BaseModel):
    """
    Represents a single chat record returned to the user.

    Attributes:
        id (str): The chat's UUID.
        title (str): The chat's title (currently unused in creation, but available for future).
        created_at (datetime): When the chat was created.
    """
    id: str
    title: Optional[str] = None
    created_at: datetime


class MessageReadSchema(BaseModel):
    """
    Represents a single message record returned from the database.

    Attributes:
        sender (str): The user or role who sent the message.
        content (str): The actual text of the message.
    """
    sender: str
    content: str


class ChatMessagesListOutputSchema(BaseModel):
    """
    Represents a list of messages returned from the 'list_chat_messages' endpoint.

    Attributes:
        messages (List[MessageReadSchema]): The messages in chronological order.
    """
    messages: List[MessageReadSchema]

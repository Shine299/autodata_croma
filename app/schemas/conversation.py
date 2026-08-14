from pydantic import Field

from app.schemas.common import CamelModel


class ConversationMessage(CamelModel):
    channel: str = "telegram"
    chat_id: str
    message_id: str
    text: str
    callback_data: str | None = None
    received_at: str


class Button(CamelModel):
    label: str
    action: str


class Reply(CamelModel):
    text: str
    parse_mode: str = "Markdown"
    buttons: list[Button] = Field(default_factory=list)


class Extracted(CamelModel):
    plate: str | None = None
    asking_price: float | None = None
    document_number: str | None = None


class ConversationResponse(CamelModel):
    chat_id: str
    state: str
    extracted: Extracted
    replies: list[Reply] = Field(default_factory=list)

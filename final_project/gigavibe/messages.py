from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal['user', 'assistant', 'system']


@dataclass
class Message:
    role: Role
    content: str

    def as_api(self) -> dict[str, str]:
        return {'role': self.role, 'content': self.content}


class ChatHistory:
    def __init__(self, limit_message: int | None = None, limit_chars: int | None = None) -> None:
        self.limit_message = limit_message
        self.limit_chars = limit_chars
        self.messages: list[Message] = []

    def add(self, role: Literal['user', 'assistant'], content: str) -> None:
        message = Message(role=role, content=self._trim_content(content))
        self.messages.append(message)
        self._trim_history()

    def reset(self) -> None:
        self.messages.clear()

    def to_api_messages(self, system_prompt: str | None = None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append(Message(role='system', content=system_prompt).as_api())
        messages.extend(message.as_api() for message in self.messages)
        return messages

    def _trim_content(self, content: str) -> str:
        if self.limit_chars is not None and len(content) > self.limit_chars:
            return content[-self.limit_chars :]
        return content

    def _trim_history(self) -> None:
        if self.limit_message is not None and len(self.messages) > self.limit_message:
            del self.messages[: len(self.messages) - self.limit_message]

        if self.limit_chars is None:
            return

        while self._chars_count() > self.limit_chars and len(self.messages) > 1:
            self.messages.pop(0)

        if self.messages and self._chars_count() > self.limit_chars:
            self.messages[0].content = self.messages[0].content[-self.limit_chars :]

    def _chars_count(self) -> int:
        return sum(len(message.content) for message in self.messages)

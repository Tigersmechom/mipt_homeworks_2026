from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from gigavibe.config import AppConfig

API_PATH = 'chat/completions'
AUTHORIZATION_HEADER = 'Authorization'
BEARER_PREFIX = 'Bearer'
CHOICES_KEY = 'choices'
CONTENT_KEY = 'content'
CONTENT_TYPE_HEADER = 'Content-Type'
DATA_PREFIX = 'data:'
DELTA_KEY = 'delta'
DONE_MARKER = '[DONE]'
JSON_CONTENT_TYPE = 'application/json'
MESSAGE_KEY = 'message'
MESSAGES_KEY = 'messages'
MODEL_KEY = 'model'
POST_METHOD = 'POST'
STREAM_KEY = 'stream'
TEMPERATURE_KEY = 'temperature'
UTF8_ENCODING = 'utf-8'


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, config: AppConfig, timeout: int = 120) -> None:
        self.config = config
        self.timeout = timeout

    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        try:
            data = self._request_json(messages)
        except (HTTPError, URLError, json.JSONDecodeError) as exc:
            raise LLMError(f'Ошибка запроса к модели: {exc}') from exc

        try:
            return str(data[CHOICES_KEY][0][MESSAGE_KEY][CONTENT_KEY])
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError('Сервер модели вернул неожиданный ответ.') from exc

    def stream_response(self, messages: Sequence[dict[str, str]]) -> Iterator[str]:
        try:
            yield from self._stream_response(messages)
        except (HTTPError, URLError, json.JSONDecodeError) as exc:
            raise LLMError(f'Ошибка streaming-запроса к модели: {exc}') from exc

    def _request_json(self, messages: Sequence[dict[str, str]]) -> Any:
        with urlopen(self._request(messages, stream=False), timeout=self.timeout) as response:
            return json.loads(response.read().decode(UTF8_ENCODING))

    def _stream_response(self, messages: Sequence[dict[str, str]]) -> Iterator[str]:
        with urlopen(self._request(messages, stream=True), timeout=self.timeout) as response:
            yield from _extract_stream_pieces(response)

    def _request(self, messages: Sequence[dict[str, str]], stream: bool) -> Request:
        payload = {
            MODEL_KEY: self.config.model,
            MESSAGES_KEY: list(messages),
            TEMPERATURE_KEY: self.config.temperature,
            STREAM_KEY: stream,
        }
        body = json.dumps(payload).encode(UTF8_ENCODING)
        return Request(
            _endpoint(self.config),
            data=body,
            headers=_headers(self.config),
            method=POST_METHOD,
        )


def _endpoint(config: AppConfig) -> str:
    return '/'.join((config.api_host, API_PATH))


def _headers(config: AppConfig) -> dict[str, str]:
    return {
        AUTHORIZATION_HEADER: '{0} {1}'.format(BEARER_PREFIX, config.api_key),
        CONTENT_TYPE_HEADER: JSON_CONTENT_TYPE,
    }


def _extract_stream_pieces(lines: Iterable[bytes]) -> Iterator[str]:
    for raw_line in lines:
        piece = extract_stream_piece(raw_line.decode(UTF8_ENCODING))
        if piece is not None:
            yield piece


def extract_stream_piece(line: str) -> str | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith(DATA_PREFIX):
        line = line.removeprefix(DATA_PREFIX).strip()
    if line == DONE_MARKER:
        return None

    data = json.loads(line)
    choice = data[CHOICES_KEY][0]
    return _content_from_choice(choice)


def _content_from_choice(choice: dict[str, object]) -> str | None:
    delta = choice.get(DELTA_KEY, {})
    content = _mapping_content(delta)
    if content is not None:
        return content

    message = choice.get(MESSAGE_KEY, {})
    return _mapping_content(message)


def _mapping_content(raw: object) -> str | None:
    if not isinstance(raw, dict):
        return None
    content = raw.get(CONTENT_KEY)
    if content is None:
        return None
    return str(content)

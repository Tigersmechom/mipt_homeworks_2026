from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AppConfig


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, config: AppConfig, timeout: int = 120) -> None:
        self.config = config
        self.timeout = timeout

    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        try:
            with urlopen(self._request(messages, stream=False), timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
        except (HTTPError, URLError, json.JSONDecodeError) as exc:
            raise LLMError(f'Ошибка запроса к модели: {exc}') from exc

        try:
            return str(data['choices'][0]['message']['content'])
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError('Сервер модели вернул неожиданный ответ.') from exc

    def stream_response(self, messages: Sequence[dict[str, str]]) -> Iterator[str]:
        try:
            with urlopen(self._request(messages, stream=True), timeout=self.timeout) as response:
                for raw_line in response:
                    piece = extract_stream_piece(raw_line.decode('utf-8'))
                    if piece is not None:
                        yield piece
        except (HTTPError, URLError, json.JSONDecodeError) as exc:
            raise LLMError(f'Ошибка streaming-запроса к модели: {exc}') from exc

    def _request(self, messages: Sequence[dict[str, str]], stream: bool) -> Request:
        payload = {
            'model': self.config.model,
            'messages': list(messages),
            'temperature': self.config.temperature,
            'stream': stream,
        }
        body = json.dumps(payload).encode('utf-8')
        return Request(
            f'{self.config.api_host}/chat/completions',
            data=body,
            headers={
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )


def extract_stream_piece(line: str) -> str | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith('data:'):
        line = line.removeprefix('data:').strip()
    if line == '[DONE]':
        return None

    data = json.loads(line)
    choice = data['choices'][0]
    delta = choice.get('delta', {})
    if 'content' in delta:
        return str(delta['content'])
    message = choice.get('message', {})
    if 'content' in message:
        return str(message['content'])
    return None

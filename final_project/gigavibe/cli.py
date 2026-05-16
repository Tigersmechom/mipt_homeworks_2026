from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from .chunks import is_chunk_command, parse_chunk_command, split_text
from .config import AppConfig, ConfigError, load_config
from .files import FileIncludeError, expand_file_mentions, read_text_file
from .llm import LLMClient, LLMError
from .messages import ChatHistory


def main() -> int:
    try:
        config = load_config()
    except ConfigError as exc:
        print(f'Ошибка конфигурации: {exc}')
        return 1

    client = LLMClient(config)
    history = ChatHistory(config.limit_message, config.limit_chars)
    print('Чат запущен. \\q - выход, /reset - новый чат, /filechunk - обработка файла.')

    while True:
        raw = input('>>> ')
        command = raw.strip()

        if command == r'\q':
            return 0
        if command == '/reset':
            history.reset()
            _clear_screen()
            continue
        if is_chunk_command(command):
            _run_file_chunk(command, config, client)
            continue
        if not command:
            continue

        try:
            message = expand_file_mentions(raw)
        except FileIncludeError as exc:
            print(exc)
            continue

        history.add('user', message)
        answer = _ask_llm(client, history.to_api_messages(config.system_prompt), config.stream)
        if answer is not None:
            history.add('assistant', answer)


def _run_file_chunk(command: str, config: AppConfig, client: LLMClient) -> None:
    try:
        options = parse_chunk_command(command)
    except ValueError as exc:
        print(exc)
        return

    path_text = input('Введите путь до файла\n>>> ').strip()
    if path_text == r'\q':
        return

    prompt = input('Принято. Что нужно сделать для каждого фрагмента?\n>>> ')
    if prompt.strip() == r'\q':
        return

    try:
        chunks = split_text(read_text_file(Path(path_text), max_bytes=None), options)
    except FileIncludeError as exc:
        print(exc)
        return

    print('Принято. Начинаю обработку:')
    for index, chunk in enumerate(chunks):
        messages = _chunk_messages(config.system_prompt, prompt, chunk)
        if _ask_llm(client, messages, config.stream) is None:
            return

        if not options.auto and index != len(chunks) - 1:
            next_command = input('>>> ').strip()
            if next_command == r'\q':
                return

    print('Обработка файла завершена.')


def _chunk_messages(
    system_prompt: str | None,
    user_prompt: str,
    chunk: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': f'{user_prompt}\n\n{chunk}'})
    return messages


def _ask_llm(
    client: LLMClient,
    messages: Sequence[dict[str, str]],
    stream: bool,
) -> str | None:
    try:
        if stream:
            parts: list[str] = []
            for piece in client.stream_response(messages):
                print(piece, end='', flush=True)
                parts.append(piece)
            print()
            return ''.join(parts)

        answer = client.complete(messages)
        print(answer)
        return answer
    except KeyboardInterrupt:
        print('\nЗапрос прерван.')
        return None
    except LLMError as exc:
        print(exc)
        return None


def _clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

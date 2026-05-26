from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from gigavibe.chunks import ChunkOptions, is_chunk_command, parse_chunk_command, split_text
from gigavibe.config import AppConfig, ConfigError, load_config
from gigavibe.files import FileIncludeError, expand_file_mentions, read_text_file
from gigavibe.llm import LLMClient, LLMError
from gigavibe.messages import ASSISTANT_ROLE, USER_ROLE, ChatHistory

CHAT_PROMPT = '>>> '
CHUNK_DONE_MESSAGE = 'Обработка файла завершена.'
CHUNK_PATH_PROMPT = 'Введите путь до файла\n>>> '
CHUNK_PROMPT = 'Принято. Что нужно сделать для каждого фрагмента?\n>>> '
CHUNK_START_MESSAGE = 'Принято. Начинаю обработку:'
CLEAR_COMMAND = 'clear'
CONFIG_ERROR_PREFIX = 'Ошибка конфигурации:'
EXIT_COMMAND = r'\q'
INTERRUPTED_MESSAGE = '\nЗапрос прерван.'
RESET_COMMAND = '/reset'
WINDOWS_CLEAR_COMMAND = 'cls'
WELCOME_MESSAGE = r'Чат запущен. \q - выход, /reset - новый чат, /filechunk - обработка файла.'


@dataclass(frozen=True)
class ChunkRequest:
    options: ChunkOptions
    prompt: str
    chunks: list[str]


def main() -> int:
    config = _load_app_config()
    if config is None:
        return 1

    client = LLMClient(config)
    history = ChatHistory(config.limit_message, config.limit_chars)
    print(WELCOME_MESSAGE)
    _run_chat(config, client, history)
    return 0


def _load_app_config() -> AppConfig | None:
    try:
        return load_config()
    except ConfigError as exc:
        print(CONFIG_ERROR_PREFIX, exc)
        return None


def _run_chat(config: AppConfig, client: LLMClient, history: ChatHistory) -> None:
    while True:
        if _handle_chat_input(config, client, history):
            return


def _handle_chat_input(config: AppConfig, client: LLMClient, history: ChatHistory) -> bool:
    raw = input(CHAT_PROMPT)
    command = raw.strip()

    if command == EXIT_COMMAND:
        return True
    if _handle_service_command(command, config, client, history):
        return False
    if not command:
        return False

    _process_user_message(raw, config, client, history)
    return False


def _handle_service_command(
    command: str,
    config: AppConfig,
    client: LLMClient,
    history: ChatHistory,
) -> bool:
    if command == RESET_COMMAND:
        history.reset()
        _clear_screen()
        return True
    if is_chunk_command(command):
        _run_file_chunk(command, config, client)
        return True
    return False


def _process_user_message(
    raw: str,
    config: AppConfig,
    client: LLMClient,
    history: ChatHistory,
) -> None:
    try:
        message = expand_file_mentions(raw)
    except FileIncludeError as exc:
        print(exc)
        return

    history.add(USER_ROLE, message)
    answer = _ask_llm(client, history.to_api_messages(config.system_prompt), config.stream)
    if answer is not None:
        history.add(ASSISTANT_ROLE, answer)


def _run_file_chunk(command: str, config: AppConfig, client: LLMClient) -> None:
    options = _read_chunk_options(command)
    if options is None:
        return

    request = _read_chunk_request(options)
    if request is None:
        return

    _process_chunks(request, config, client)


def _read_chunk_options(command: str) -> ChunkOptions | None:
    try:
        return parse_chunk_command(command)
    except ValueError as exc:
        print(exc)
        return None


def _read_chunk_request(options: ChunkOptions) -> ChunkRequest | None:
    path_text = input(CHUNK_PATH_PROMPT).strip()
    if path_text == EXIT_COMMAND:
        return None

    prompt = input(CHUNK_PROMPT)
    if prompt.strip() == EXIT_COMMAND:
        return None

    chunks = _read_chunks(path_text, options)
    if chunks is None:
        return None
    return ChunkRequest(options=options, prompt=prompt, chunks=chunks)


def _read_chunks(path_text: str, options: ChunkOptions) -> list[str] | None:
    try:
        return split_text(read_text_file(Path(path_text), max_bytes=None), options)
    except FileIncludeError as exc:
        print(exc)
        return None


def _process_chunks(request: ChunkRequest, config: AppConfig, client: LLMClient) -> None:
    print(CHUNK_START_MESSAGE)
    for index, chunk in enumerate(request.chunks):
        if not _process_chunk(request.prompt, chunk, config, client):
            return
        if _should_wait_for_next_chunk(request.options, index, request.chunks):
            if input(CHAT_PROMPT).strip() == EXIT_COMMAND:
                return

    print(CHUNK_DONE_MESSAGE)


def _process_chunk(
    prompt: str,
    chunk: str,
    config: AppConfig,
    client: LLMClient,
) -> bool:
    messages = _chunk_messages(config.system_prompt, prompt, chunk)
    return _ask_llm(client, messages, config.stream) is not None


def _should_wait_for_next_chunk(
    options: ChunkOptions,
    index: int,
    chunks: Sequence[str],
) -> bool:
    return not options.auto and index != len(chunks) - 1


def _chunk_messages(
    system_prompt: str | None,
    user_prompt: str,
    chunk: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': USER_ROLE, 'content': '{0}\n\n{1}'.format(user_prompt, chunk)})
    return messages


def _ask_llm(
    client: LLMClient,
    messages: Sequence[dict[str, str]],
    stream: bool,
) -> str | None:
    try:
        return _request_llm_answer(client, messages, stream)
    except KeyboardInterrupt:
        print(INTERRUPTED_MESSAGE)
        return None
    except LLMError as exc:
        print(exc)
        return None


def _request_llm_answer(
    client: LLMClient,
    messages: Sequence[dict[str, str]],
    stream: bool,
) -> str:
    if stream:
        return _stream_llm_answer(client, messages)
    return _complete_llm_answer(client, messages)


def _stream_llm_answer(client: LLMClient, messages: Sequence[dict[str, str]]) -> str:
    parts: list[str] = []
    for piece in client.stream_response(messages):
        print(piece, end='', flush=True)
        parts.append(piece)
    print()
    return ''.join(parts)


def _complete_llm_answer(client: LLMClient, messages: Sequence[dict[str, str]]) -> str:
    answer = client.complete(messages)
    print(answer)
    return answer


def _clear_screen() -> None:
    command = WINDOWS_CLEAR_COMMAND if os.name == 'nt' else CLEAR_COMMAND
    os.system(command)

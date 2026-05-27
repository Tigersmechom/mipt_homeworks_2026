from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Literal

PARAGRAPH_MODE: Literal['paragraph'] = 'paragraph'
LENGTH_MODE: Literal['len'] = 'len'
AUTO_APPROVE_FLAG = '-y'
OPTION_SEPARATOR = '='

ChunkMode = Literal['paragraph', 'len']
CHUNK_COMMANDS = frozenset(('/filechunk', '/file_chunk'))


@dataclass(frozen=True)
class ChunkOptions:
    mode: ChunkMode = PARAGRAPH_MODE
    size: int = 1
    auto: bool = False


def is_chunk_command(text: str) -> bool:
    parts = text.strip().split(maxsplit=1)
    return bool(parts and parts[0] in CHUNK_COMMANDS)


def parse_chunk_command(text: str) -> ChunkOptions:
    parts = shlex.split(text)
    if not parts or parts[0] not in CHUNK_COMMANDS:
        raise ValueError('Неизвестная команда обработки файла.')

    return _parse_chunk_options(parts[1:])


def _parse_chunk_options(tokens: list[str]) -> ChunkOptions:
    options = ChunkOptions()
    for token in tokens:
        options = _update_options(options, token)
    if options.size <= 0:
        raise ValueError('Размер чанка должен быть положительным.')
    return options


def _update_options(options: ChunkOptions, token: str) -> ChunkOptions:
    if token == AUTO_APPROVE_FLAG:
        return ChunkOptions(mode=options.mode, size=options.size, auto=True)
    if token.startswith(f'{PARAGRAPH_MODE}{OPTION_SEPARATOR}'):
        return ChunkOptions(mode=PARAGRAPH_MODE, size=_option_size(token), auto=options.auto)
    if token.startswith(f'{LENGTH_MODE}{OPTION_SEPARATOR}'):
        return ChunkOptions(mode=LENGTH_MODE, size=_option_size(token), auto=options.auto)
    raise ValueError(f'Неизвестный аргумент: {token}')


def _option_size(token: str) -> int:
    return int(token.split(OPTION_SEPARATOR, 1)[1])


def split_text(text: str, options: ChunkOptions) -> list[str]:
    if options.mode == LENGTH_MODE:
        return _split_by_length(text, options.size)

    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    return _split_paragraphs(paragraphs, options.size)


def _split_by_length(text: str, size: int) -> list[str]:
    chunks: list[str] = []
    for start in range(0, len(text), size):
        if text[start]:
            chunks.append(text[start : start + size])
    return chunks


def _split_paragraphs(paragraphs: list[str], size: int) -> list[str]:
    chunks: list[str] = []
    for start in range(0, len(paragraphs), size):
        chunks.append('\n'.join(paragraphs[start : start + size]))
    return chunks

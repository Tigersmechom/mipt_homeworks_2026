from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Literal

ChunkMode = Literal['paragraph', 'len']
CHUNK_COMMANDS = {'/filechunk', '/file_chunk'}


@dataclass(frozen=True)
class ChunkOptions:
    mode: ChunkMode = 'paragraph'
    size: int = 1
    auto: bool = False


def is_chunk_command(text: str) -> bool:
    parts = text.strip().split(maxsplit=1)
    return bool(parts and parts[0] in CHUNK_COMMANDS)


def parse_chunk_command(text: str) -> ChunkOptions:
    parts = shlex.split(text)
    if not parts or parts[0] not in CHUNK_COMMANDS:
        raise ValueError('Неизвестная команда обработки файла.')

    mode: ChunkMode = 'paragraph'
    size = 1
    auto = False

    for token in parts[1:]:
        if token == '-y':
            auto = True
        elif token.startswith('paragraph='):
            mode = 'paragraph'
            size = int(token.split('=', 1)[1])
        elif token.startswith('len='):
            mode = 'len'
            size = int(token.split('=', 1)[1])
        else:
            raise ValueError(f'Неизвестный аргумент: {token}')

    if size <= 0:
        raise ValueError('Размер чанка должен быть положительным.')
    return ChunkOptions(mode=mode, size=size, auto=auto)


def split_text(text: str, options: ChunkOptions) -> list[str]:
    if options.mode == 'len':
        return [text[i : i + options.size] for i in range(0, len(text), options.size) if text[i]]

    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    return [
        '\n'.join(paragraphs[i : i + options.size]) for i in range(0, len(paragraphs), options.size)
    ]

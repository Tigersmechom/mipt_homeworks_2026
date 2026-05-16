from __future__ import annotations

import re
from pathlib import Path

MAX_INCLUDE_BYTES = 5 * 1024 * 1024
MENTION_RE = re.compile(r'@::(.+?)::')


class FileIncludeError(ValueError):
    pass


def expand_file_mentions(text: str) -> str:
    return MENTION_RE.sub(lambda match: '\n' + read_text_file(Path(match.group(1))).rstrip(), text)


def read_text_file(path: Path, max_bytes: int | None = MAX_INCLUDE_BYTES) -> str:
    path = path.expanduser()
    try:
        if max_bytes is not None and path.stat().st_size > max_bytes:
            raise FileIncludeError(f'Файл больше {max_bytes // 1024 // 1024} МБ: {path}')
        return path.read_text(encoding='utf-8')
    except OSError as exc:
        raise FileIncludeError(f'Не удалось прочитать файл {path}: {exc}') from exc
    except UnicodeDecodeError as exc:
        raise FileIncludeError(f'Файл не похож на UTF-8 текст: {path}') from exc

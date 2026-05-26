from __future__ import annotations

import re
from pathlib import Path

MAX_INCLUDE_BYTES = 5 * 1024 * 1024
BYTES_IN_MEGABYTE = 1024 * 1024
MENTION_RE = re.compile(r'@::(.+?)::')


class FileIncludeError(ValueError):
    pass


def expand_file_mentions(text: str) -> str:
    return MENTION_RE.sub(_replace_file_mention, text)


def _replace_file_mention(match: re.Match[str]) -> str:
    file_text = read_text_file(Path(match.group(1))).rstrip()
    return '\n{0}'.format(file_text)


def read_text_file(path: Path, max_bytes: int | None = MAX_INCLUDE_BYTES) -> str:
    path = path.expanduser()
    try:
        _ensure_file_size(path, max_bytes)
    except OSError as exc:
        raise FileIncludeError(f'Не удалось прочитать файл {path}: {exc}') from exc

    try:
        return path.read_text(encoding='utf-8')
    except OSError as exc:
        raise FileIncludeError(f'Не удалось прочитать файл {path}: {exc}') from exc
    except UnicodeDecodeError as exc:
        raise FileIncludeError(f'Файл не похож на UTF-8 текст: {path}') from exc


def _ensure_file_size(path: Path, max_bytes: int | None) -> None:
    if max_bytes is None:
        return
    if path.stat().st_size <= max_bytes:
        return

    limit_mb = max_bytes // BYTES_IN_MEGABYTE
    raise FileIncludeError(f'Файл больше {limit_mb} МБ: {path}')

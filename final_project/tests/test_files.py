from pathlib import Path

import pytest

from gigavibe.files import FileIncludeError, expand_file_mentions, read_text_file


def test_expand_file_mentions_inserts_file_text(tmp_path: Path) -> None:
    file_path = tmp_path / 'main.py'
    file_path.write_text('print(1)\n', encoding='utf-8')

    result = expand_file_mentions(f'check @::{file_path}::')

    assert result == 'check \nprint(1)'


def test_read_text_file_checks_size(tmp_path: Path) -> None:
    file_path = tmp_path / 'big.txt'
    file_path.write_text('123456', encoding='utf-8')

    with pytest.raises(FileIncludeError):
        read_text_file(file_path, max_bytes=5)

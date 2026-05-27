from gigavibe.chunks import ChunkOptions, is_chunk_command, parse_chunk_command, split_text


def test_parse_chunk_command() -> None:
    options = parse_chunk_command('/filechunk paragraph=2 -y')

    assert options == ChunkOptions(mode='paragraph', size=2, auto=True)


def test_file_chunk_alias_is_supported() -> None:
    assert is_chunk_command('/file_chunk len=10')


def test_split_by_paragraph_groups_lines() -> None:
    chunks = split_text('one\n\ntwo\nthree', ChunkOptions(mode='paragraph', size=2))

    assert chunks == ['one\ntwo', 'three']


def test_split_by_len() -> None:
    chunks = split_text('abcdef', ChunkOptions(mode='len', size=2))

    assert chunks == ['ab', 'cd', 'ef']

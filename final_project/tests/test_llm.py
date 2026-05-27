from gigavibe.llm import extract_stream_piece


def test_extract_stream_piece_from_delta() -> None:
    line = 'data: {"choices": [{"delta": {"content": "hello"}}]}'

    assert extract_stream_piece(line) == 'hello'


def test_extract_stream_piece_ignores_done() -> None:
    assert extract_stream_piece('data: [DONE]') is None

from gigavibe.messages import ChatHistory


def test_limit_message_removes_oldest_messages() -> None:
    history = ChatHistory(limit_message=2)

    history.add('user', 'one')
    history.add('assistant', 'two')
    history.add('user', 'three')

    assert [message.content for message in history.messages] == ['two', 'three']


def test_limit_chars_removes_oldest_messages() -> None:
    history = ChatHistory(limit_chars=5)

    history.add('user', 'abc')
    history.add('assistant', 'def')

    assert [message.content for message in history.messages] == ['def']


def test_single_too_long_message_is_trimmed_from_left() -> None:
    history = ChatHistory(limit_chars=4)

    history.add('user', 'abcdef')

    assert history.messages[0].content == 'cdef'


def test_system_prompt_is_added_to_api_messages() -> None:
    history = ChatHistory()
    history.add('user', 'hello')

    assert history.to_api_messages('system') == [
        {'role': 'system', 'content': 'system'},
        {'role': 'user', 'content': 'hello'},
    ]

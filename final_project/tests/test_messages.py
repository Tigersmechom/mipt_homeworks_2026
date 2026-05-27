from gigavibe.messages import ASSISTANT_ROLE, USER_ROLE, ChatHistory


def test_limit_message_removes_oldest_messages() -> None:
    history = ChatHistory(limit_message=2)

    history.add(USER_ROLE, 'one')
    history.add(ASSISTANT_ROLE, 'two')
    history.add(USER_ROLE, 'three')

    assert [message.content for message in history.messages] == ['two', 'three']


def test_limit_chars_removes_oldest_messages() -> None:
    history = ChatHistory(limit_chars=5)

    history.add(USER_ROLE, 'abc')
    history.add(ASSISTANT_ROLE, 'def')

    assert [message.content for message in history.messages] == ['def']


def test_long_message_is_trimmed_from_left() -> None:
    history = ChatHistory(limit_chars=4)

    history.add(USER_ROLE, 'abcdef')

    assert history.messages[0].content == 'cdef'


def test_system_prompt_is_added_to_api_messages() -> None:
    history = ChatHistory()
    history.add(USER_ROLE, 'hello')

    assert history.to_api_messages('system') == [
        {'role': 'system', 'content': 'system'},
        {'role': 'user', 'content': 'hello'},
    ]

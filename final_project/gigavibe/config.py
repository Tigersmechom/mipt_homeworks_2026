from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_MODEL = 'gemma3:270m'
DEFAULT_CONFIG_PATH = Path('config.yaml')
API_KEY_ENV = 'API_KEY'
API_HOST_ENV = 'API_HOST'
MODEL_ENV = 'MODEL'
LIMIT_MESSAGE_ENV = 'LIMIT_MESSAGE'
LIMIT_MESSAGES_ENV = 'LIMIT_MESSAGES'
LIMIT_CHARS_ENV = 'LIMIT_CHARS'
TEMPERATURE_ENV = 'TEMPERATURE'
STREAM_ENV = 'STREAM'

API_KEY_KEY = 'api_key'
API_HOST_KEY = 'api_host'
MODEL_KEY = 'model'
LIMIT_MESSAGE_KEY = 'limit_message'
LIMIT_CHARS_KEY = 'limit_chars'
TEMPERATURE_KEY = 'temperature'
SYSTEM_PROMPT_KEY = 'system_prompt'
STREAM_KEY = 'stream'
TRUE_VALUES = frozenset(('1', 'true', 'yes', 'y', 'on'))
ENV_KEYS = (
    (API_KEY_ENV, API_KEY_KEY),
    (API_HOST_ENV, API_HOST_KEY),
    (MODEL_ENV, MODEL_KEY),
    (LIMIT_MESSAGE_ENV, LIMIT_MESSAGE_KEY),
    (LIMIT_MESSAGES_ENV, LIMIT_MESSAGE_KEY),
    (LIMIT_CHARS_ENV, LIMIT_CHARS_KEY),
    (TEMPERATURE_ENV, TEMPERATURE_KEY),
    (STREAM_ENV, STREAM_KEY),
)


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    api_host: str
    model: str = DEFAULT_MODEL
    limit_message: int | None = None
    limit_chars: int | None = None
    temperature: float = 0.7
    system_prompt: str | None = None
    stream: bool = False


def load_config(
    path: Path = DEFAULT_CONFIG_PATH,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    env = os.environ if env is None else env
    raw = _load_yaml(path)

    has_config = path.exists() and bool(raw)
    if not has_config and not _has_env_config(env):
        raise ConfigError('Нет config.yaml и нужных переменных окружения.')

    for env_key, config_key in ENV_KEYS:
        env_value = env.get(env_key)
        if env_value is not None:
            raw[config_key] = env_value

    api_key = _required_str(raw, API_KEY_KEY)
    api_host = _required_str(raw, API_HOST_KEY)

    return AppConfig(
        api_key=api_key,
        api_host=api_host.rstrip('/'),
        model=str(raw.get(MODEL_KEY) or DEFAULT_MODEL),
        limit_message=_optional_int(raw.get(LIMIT_MESSAGE_KEY), LIMIT_MESSAGE_KEY),
        limit_chars=_optional_int(raw.get(LIMIT_CHARS_KEY), LIMIT_CHARS_KEY),
        temperature=_temperature(raw.get(TEMPERATURE_KEY, 0.7)),
        system_prompt=_optional_str(raw.get(SYSTEM_PROMPT_KEY)),
        stream=_bool(raw.get(STREAM_KEY, False)),
    )


def _has_env_config(env: Mapping[str, str]) -> bool:
    for env_key, _ in ENV_KEYS:
        if env.get(env_key) is not None:
            return True
    return False


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        raise ConfigError('config.yaml содержит некорректный YAML.') from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError('config.yaml должен быть YAML-словарем.')
    return dict(data)


def _required_str(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if value is None or str(value).strip() == '':
        raise ConfigError(f'Не задан параметр {key}.')
    return str(value)


def _optional_str(value: Any) -> str | None:
    if value is None or str(value).strip() == '':
        return None
    return str(value)


def _optional_int(value: Any, name: str) -> int | None:
    if value is None or str(value).strip() == '':
        return None
    try:
        result = int(value)
    except ValueError as exc:
        raise ConfigError(f'{name} должен быть целым числом.') from exc
    if result <= 0:
        raise ConfigError(f'{name} должен быть положительным числом.')
    return result


def _temperature(value: Any) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise ConfigError('temperature должен быть числом.') from exc
    if not 0 <= result <= 1:
        raise ConfigError('temperature должен быть от 0 до 1.')
    return result


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    return normalized in TRUE_VALUES

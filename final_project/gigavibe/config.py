from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

DEFAULT_MODEL = 'gemma3:270m'
ENV_KEYS = {
    'API_KEY': 'api_key',
    'API_HOST': 'api_host',
    'MODEL': 'model',
    'LIMIT_MESSAGE': 'limit_message',
    'LIMIT_MESSAGES': 'limit_message',
    'LIMIT_CHARS': 'limit_chars',
    'TEMPERATURE': 'temperature',
    'STREAM': 'stream',
}


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
    path: Path = Path('config.yaml'),
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    env = os.environ if env is None else env
    raw = _load_yaml(path)

    has_config = path.exists() and bool(raw)
    has_env = any(key in env for key in ENV_KEYS)
    if not has_config and not has_env:
        raise ConfigError('Нет config.yaml и нужных переменных окружения.')

    for env_key, config_key in ENV_KEYS.items():
        if env_key in env:
            raw[config_key] = env[env_key]

    api_key = _required_str(raw, 'api_key')
    api_host = _required_str(raw, 'api_host')

    return AppConfig(
        api_key=api_key,
        api_host=api_host.rstrip('/'),
        model=str(raw.get('model') or DEFAULT_MODEL),
        limit_message=_optional_int(raw.get('limit_message'), 'limit_message'),
        limit_chars=_optional_int(raw.get('limit_chars'), 'limit_chars'),
        temperature=_temperature(raw.get('temperature', 0.7)),
        system_prompt=_optional_str(raw.get('system_prompt')),
        stream=_bool(raw.get('stream', False)),
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
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
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

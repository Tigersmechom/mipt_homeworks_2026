from pathlib import Path

import pytest

from gigavibe.config import ConfigError, load_config


def test_load_config_env_overrides_yaml(tmp_path: Path) -> None:
    path = tmp_path / 'config.yaml'
    path.write_text(
        '\n'.join(
            [
                'api_key: yaml-key',
                'api_host: http://yaml/v1',
                'limit_message: 3',
                'temperature: 0.2',
            ]
        ),
        encoding='utf-8',
    )

    config = load_config(
        path,
        {
            'API_KEY': 'env-key',
            'API_HOST': 'http://env/v1/',
            'LIMIT_CHARS': '100',
            'STREAM': 'true',
        },
    )

    assert config.api_key == 'env-key'
    assert config.api_host == 'http://env/v1'
    assert config.limit_message == 3
    assert config.limit_chars == 100
    assert config.temperature == 0.2
    assert config.stream is True


def test_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / 'missing.yaml', {})


def test_invalid_yaml_raises_config_error(tmp_path: Path) -> None:
    path = tmp_path / 'config.yaml'
    path.write_text('api_key: [broken\n', encoding='utf-8')

    with pytest.raises(ConfigError, match='некорректный YAML'):
        load_config(path, {})


def test_non_mapping_yaml_raises_config_error(tmp_path: Path) -> None:
    path = tmp_path / 'config.yaml'
    path.write_text('- api_key\n- api_host\n', encoding='utf-8')

    with pytest.raises(ConfigError, match='YAML-словарем'):
        load_config(path, {})


def test_invalid_temperature_raises(tmp_path: Path) -> None:
    path = tmp_path / 'config.yaml'
    path.write_text(
        'api_key: key\napi_host: http://host/v1\ntemperature: 2\n',
        encoding='utf-8',
    )

    with pytest.raises(ConfigError):
        load_config(path, {})

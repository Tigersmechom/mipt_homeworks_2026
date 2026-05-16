# GigaVibeMiptCode

Консольный чат-бот для OpenAI-compatible LLM API. Подходит для Ollama, LM Studio, OpenRouter и похожих провайдеров.

## Установка

```bash
cd final_project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Настройка

Можно использовать переменные окружения:

```bash
export API_KEY=your_key_here
export API_HOST=http://localhost:11434/v1/
export MODEL=gemma3:270m
export LIMIT_CHARS=2000
export LIMIT_MESSAGE=20
export TEMPERATURE=0.7
export STREAM=true
python final_project/main.py
```

Или создать `config.yaml` по примеру:

```yaml
api_key: your_key_here
api_host: http://localhost:11434/v1/
model: gemma3:270m
limit_message: 20
limit_chars: 2000
temperature: 0.7
stream: true
system_prompt: You are a helpful Python assistant.
```

Переменные окружения имеют приоритет над `config.yaml`. Файл `config.yaml` может содержать секреты, поэтому его не стоит коммитить.

## Запуск

```bash
cd final_project
python main.py
```

Команды:

- `\q` - выход из основного чата или режима обработки файла.
- `/reset` - очистить историю сообщений и экран.
- `/filechunk`, `/file_chunk` - обработать файл по частям.

Примеры режима чанков:

```text
/filechunk
/filechunk paragraph=3
/filechunk len=150
/filechunk paragraph=3 -y
```

Файлы можно прикреплять к сообщению так:

```text
В чем ошибка? @::/path/to/main.py::
```

## Проверки

```bash
ruff check --config final_project/ruff.toml final_project
mypy final_project
pytest -q final_project/tests
coverage run --source=final_project/gigavibe -m pytest -q final_project/tests
coverage html -d final_project/htmlcov
```

HTML-отчет покрытия создается в `final_project/htmlcov/index.html`.

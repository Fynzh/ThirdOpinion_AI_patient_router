"""Обёртка над GigaChat. Отделена от analyzer.py — чтобы можно было
заменить модель, не трогая медицинскую логику.
"""

import os

from dotenv import load_dotenv
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

load_dotenv()

GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")

# GigaChat-клиент создаём один раз и переиспользуем —
# иначе на каждый запрос будет новая авторизация (медленно).
_client = None


def _get_client() -> GigaChat:
    global _client
    if _client is None:
        if not GIGACHAT_KEY:
            raise RuntimeError(
                "GIGACHAT_KEY не найден. Проверь .env-файл в корне проекта."
            )
        _client = GigaChat(
            credentials=GIGACHAT_KEY,
            scope="GIGACHAT_API_PERS",
            model="GigaChat-2",
            verify_ssl_certs=False,
        ) # для macOS; в продакшене убрать
    return _client


def call_llm(prompt: str) -> str:
    """Отправляет промпт в GigaChat, возвращает текст ответа.

    Используется в analyzer.generate_recommendations как call_llm.
    Температура низкая — нам нужен стабильный JSON, а не креатив.
    """
    client = _get_client()
    payload = Chat(
        messages=[Messages(role=MessagesRole.USER, content=prompt)],
        temperature=0.1,
    )
    response = client.chat(payload)
    return response.choices[0].message.content
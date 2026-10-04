"""
Реестр персональных данных пациентов.

Хранит соответствие patient_code → {ФИО, дата рождения, телефон, email}.
Данные лежат в JSON-файле рядом с manage.py.
Файл НЕ коммитится в Git — добавлен в .gitignore.
"""

import json
from pathlib import Path
from threading import Lock

# Путь: рядом с manage.py (на уровень выше core/)
REGISTRY_PATH = Path(__file__).resolve().parent.parent / "patient_registry.json"

# Блокировка на случай одновременных запросов
_lock = Lock()


def _load() -> dict:
    """Читает JSON-файл. Если файла нет — возвращает пустой словарь."""
    if not REGISTRY_PATH.exists():
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    """Сохраняет данные в JSON-файл."""
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_personal_data(patient_code: str) -> dict | None:
    """Возвращает личные данные по коду пациента. None — если не найдено."""
    return _load().get(patient_code)


def set_personal_data(patient_code: str, data: dict) -> None:
    """Сохраняет личные данные пациента. Перезаписывает старые."""
    with _lock:
        registry = _load()
        registry[patient_code] = data
        _save(registry)


def update_personal_data(patient_code: str, **fields) -> None:
    """Обновляет отдельные поля личных данных."""
    with _lock:
        registry = _load()
        if patient_code not in registry:
            registry[patient_code] = {}
        registry[patient_code].update(fields)
        _save(registry)


def delete_personal_data(patient_code: str) -> None:
    """Удаляет личные данные пациента."""
    with _lock:
        registry = _load()
        registry.pop(patient_code, None)
        _save(registry)


def all_codes() -> list[str]:
    """Возвращает список всех кодов пациентов в реестре."""
    return list(_load().keys())
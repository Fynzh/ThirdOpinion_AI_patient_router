"""
NLP-модуль для анализа заключений рентгенолога.

⚠️ ВНИМАНИЕ: это ЗАГЛУШКА.
Настоящую модель напишет NLP-разработчик.
Заменяется одна функция — вся остальная система не меняется.
"""


def generate_recommendations(radiologist_conclusion: str, patient_info: dict = None) -> dict:
    """
    Принимает текст заключения рентгенолога и возвращает рекомендации.

    Аргументы:
        radiologist_conclusion: текст заключения
        patient_info: словарь с данными пациента (опционально)

    Возвращает:
        {
            "recommendations": [
                {
                    "specialist": "проктолог",
                    "specialty_code": "PROCTO",
                    "reasoning": "...",
                    "priority": "high",
                    "confidence": 0.87
                },
                ...
            ],
            "summary": "Краткое резюме",
            "error": None
        }
    """
    # ⚠️ ЗАГЛУШКА — вернёт одинаковые рекомендации для любого текста
    return {
        "recommendations": [
            {
                "specialist": "проктолог",
                "specialty_code": "PROCTO",
                "reasoning": "В заключении описано образование, требующее осмотра профильного специалиста.",
                "priority": "high",
                "confidence": 0.82
            },
            {
                "specialist": "невролог",
                "specialty_code": "NEURO",
                "reasoning": "Упоминаются симптомы, требующие уточнения у невролога.",
                "priority": "medium",
                "confidence": 0.65
            }
        ],
        "summary": "Рекомендуется консультация проктолога и невролога.",
        "error": None
    }
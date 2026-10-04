"""
Сигналы приложения core.

Автоматически запускают ИИ-анализ при создании нового исследования.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Study

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Study)
def auto_run_ai_on_new_study(sender, instance: Study, created: bool, **kwargs):
    """
    Запускает ИИ-анализ сразу после создания нового исследования.
    Срабатывает ТОЛЬКО при создании (created=True), не при обновлении.
    """
    if not created:
        return

    # Защита от пустого заключения
    if not instance.radiologist_conclusion or not instance.radiologist_conclusion.strip():
        logger.warning(
            "Study #%s создан без заключения — ИИ не запущен", instance.id
        )
        return

    # Импорты внутри функции — чтобы Django не падал при загрузке,
    # если NLP-модуль недоступен
    from nlp_module.analyzer import (
        generate_recommendations,
        RecommendationError,
    )
    from nlp_module.llm import call_llm
    from .models import Recommendation

    # Удаляем старые рекомендации от ИИ (если вдруг есть)
    instance.recommendations.filter(source="ai").delete()

    try:
        result = generate_recommendations(
            radiologist_conclusion=instance.radiologist_conclusion,
            call_llm=call_llm,
            patient_age=instance.patient.age,
            patient_sex=instance.patient.sex,
        )
    except RecommendationError as e:
        logger.error("Study #%s: NLP вернул мусор — %s", instance.id, e)
        return
    except Exception as e:
        logger.error(
            "Study #%s: ошибка NLP — %s: %s",
            instance.id, type(e).__name__, e,
        )
        return

    # Сохраняем рекомендации
    for rec in result.get("recommendations", []):
        Recommendation.objects.create(
            study=instance,
            source="ai",
            status="pending",
            specialist=rec["specialist"],
            specialty_code=rec["specialty_code"],
            reasoning=rec["reasoning"],
            priority=rec["priority"],
            confidence=rec.get("confidence"),
            raw_model_output=rec,
        )

    # Обновляем статус исследования
    if result.get("status") == "no_findings":
        instance.status = "approved"
    else:
        instance.status = "ai_done"

    # save() через queryset.update() — чтобы НЕ дёрнуть сигнал повторно
    Study.objects.filter(id=instance.id).update(status=instance.status)

    logger.info(
        "Study #%s: ИИ обработал автоматически, статус=%s",
        instance.id, instance.status,
    )


from django.db.models.signals import pre_save
from .models import Recommendation


@receiver(pre_save, sender=Recommendation)
def auto_mark_edited(sender, instance: Recommendation, **kwargs):
    """
    Автоматически ставит статус 'edited', если врач изменил
    ключевые поля рекомендации (специалист, обоснование, приоритет).

    НЕ трогает рекомендации от врача (source='doctor').
    НЕ трогает, если статус уже был approved/rejected.
    """
    # Новую рекомендацию не трогаем
    if not instance.pk:
        return

    # Рекомендации от врача — его собственные, статус уже approved
    if instance.source != "ai":
        return

    # Достаём старое состояние из БД
    try:
        old = Recommendation.objects.get(pk=instance.pk)
    except Recommendation.DoesNotExist:
        return

    # Если статус уже approved/rejected — не перезаписываем
    if old.status in ("approved", "rejected"):
        return

    # Проверяем, изменились ли ключевые поля
    fields_changed = (
            old.specialist != instance.specialist
            or old.reasoning != instance.reasoning
            or old.priority != instance.priority
    )

    if fields_changed:
        instance.status = "edited"
        logger.info(
            "Recommendation #%s: врач изменил поля → статус 'edited'",
            instance.pk,
        )
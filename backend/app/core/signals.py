"""
Сигналы приложения core.

- auto_run_ai_on_new_study:    запускает ИИ при создании исследования
- auto_reset_status_on_edit:   сбрасывает рекомендацию в 'pending' при правке
- update_study_and_create_plan: авто-создаёт CarePlan, когда все рекомендации проверены
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Study, Recommendation, CarePlan

logger = logging.getLogger(__name__)


# ============================================================
# 1. АВТОЗАПУСК ИИ ПРИ СОЗДАНИИ ИССЛЕДОВАНИЯ
# ============================================================
@receiver(post_save, sender=Study)
def auto_run_ai_on_new_study(sender, instance: Study, created: bool, **kwargs):
    """
    Запускает ИИ-анализ сразу после создания нового исследования.
    Срабатывает ТОЛЬКО при создании (created=True).
    """
    if not created:
        return

    if not instance.radiologist_conclusion or not instance.radiologist_conclusion.strip():
        logger.warning(
            "Study #%s создан без заключения — ИИ не запущен", instance.id
        )
        return

    from nlp_module.analyzer import (
        generate_recommendations,
        RecommendationError,
    )
    from nlp_module.llm import call_llm

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

    if result.get("status") == "no_findings":
        instance.status = "approved"
    else:
        instance.status = "ai_done"

    Study.objects.filter(id=instance.id).update(status=instance.status)

    logger.info(
        "Study #%s: ИИ обработал автоматически, статус=%s",
        instance.id, instance.status,
    )


# ============================================================
# 2. СБРОС РЕКОМЕНДАЦИИ В 'pending' ПРИ ПРАВКЕ
# ============================================================
@receiver(pre_save, sender=Recommendation)
def auto_reset_status_on_edit(sender, instance: Recommendation, **kwargs):
    """
    Любое изменение содержимого рекомендации:
    - переводит авторство врачу (source='doctor');
    - сбрасывает статус в 'pending'.
    """
    if not instance.pk:
        return

    try:
        old = Recommendation.objects.get(pk=instance.pk)
    except Recommendation.DoesNotExist:
        return

    def _norm(v):
        return (v or "").strip() if isinstance(v, str) else v

    content_changed = (
        _norm(old.specialist) != _norm(instance.specialist)
        or _norm(old.specialty_code) != _norm(instance.specialty_code)
        or _norm(old.reasoning) != _norm(instance.reasoning)
        or old.priority != instance.priority
        or old.confidence != instance.confidence
    )

    if not content_changed:
        return

    instance.source = "doctor"
    instance.status = "pending"
    logger.info(
        "Recommendation #%s: правка → source='doctor', status='pending'",
        instance.pk,
    )


# ============================================================
# 3. АВТОСОЗДАНИЕ ПЛАНА, КОГДА ВСЕ РЕКОМЕНДАЦИИ ПРОВЕРЕНЫ
# ============================================================
@receiver(post_save, sender=Recommendation)
def update_study_and_create_plan(sender, instance: Recommendation, **kwargs):
    """
    Когда все рекомендации исследования проверены (approved/rejected):
    - переводит Study в статус 'in_review';
    - автоматически создаёт/обновляет CarePlan со статусом 'draft'.

    Если план уже 'sent' — не трогает.
    """
    study = instance.study

    # Если план уже отправлен — не трогаем
    if hasattr(study, "care_plan") and study.care_plan.status == "sent":
        return

    # Если есть хоть одна pending — ещё рано
    has_pending = study.recommendations.filter(status="pending").exists()
    if has_pending:
        return

    # Все проверены — собираем snapshot одобренных
    approved = study.recommendations.filter(status="approved").values(
        "specialist", "reasoning", "priority"
    )
    approved_list = list(approved)

    CarePlan.objects.update_or_create(
        study=study,
        defaults={
            "recommendations_snapshot": approved_list,
            "status": "draft",
        },
    )

    # Обновляем статус исследования — если ещё не approved/sent
    if study.status not in ("approved", "sent"):
        Study.objects.filter(id=study.id).update(status="in_review")
        logger.info(
            "Study #%s: все рекомендации проверены → создан CarePlan, status='in_review'",
            study.id,
        )
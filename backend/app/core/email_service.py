"""
Отправка плана пациента по email.
На хакатоне — заглушка: письмо печатается в консоль.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .patient_registry import get_personal_data


def send_care_plan_email(plan) -> bool:
    """
    Отправляет план пациента по email.
    Возвращает True при успехе, False — если email не найден.
    """
    patient_code = plan.study.patient.patient_code
    personal = get_personal_data(patient_code) or {}
    email = personal.get("email")

    if not email:
        return False

    full_name = personal.get("full_name", "Пациент")
    birth_date = personal.get("birth_date", "не указана")
    phone = personal.get("phone", "не указан")

    patient = plan.study.patient
    study = plan.study

    # ---- Формируем блоки рекомендаций ----
    recommendations_text = ""
    for i, rec in enumerate(plan.recommendations_snapshot, start=1):
        priority_map = {"high": "СРОЧНО", "medium": "Планово", "low": "Профилактически"}
        priority = priority_map.get(rec.get("priority", "medium"), "")
        recommendations_text += (
            f"\n{i}. {rec['specialist'].upper()} — {priority}\n"
            f"   {rec['reasoning']}\n"
        )

    # ---- Формируем письмо ----
    subject = f"План обращения по исследованию от {study.study_date}"

    body = f"""Здравствуйте, {full_name}!

По результатам вашего исследования ({study.get_modality_display()}
от {study.study_date}) врач составил персональный план дальнейших действий.

════════════════════════════════════════
ДАННЫЕ ПАЦИЕНТА
════════════════════════════════════════
ФИО:            {full_name}
Дата рождения:  {birth_date}
Возраст:        {patient.age}
Пол:            {patient.get_sex_display()}
Телефон:        {phone}

════════════════════════════════════════
ЗАКЛЮЧЕНИЕ РЕНТГЕНОЛОГА
════════════════════════════════════════
{study.radiologist_conclusion}

════════════════════════════════════════
РЕКОМЕНДУЕМЫЙ ПЛАН
════════════════════════════════════════
{recommendations_text}

════════════════════════════════════════
Чтобы записаться на приём, позвоните нам:
{settings.CLINIC_PHONE}

С уважением,
Клиника «Третье мнение»
"""


    # ---- Читаемый вывод в консоль (для демо) ----
    print("\n" + "=" * 70)
    print(f"📧 ПИСЬМО ПАЦИЕНТУ")
    print(f"Кому: {email}")
    print(f"Тема: {subject}")
    print("=" * 70)
    print(body)
    print("=" * 70 + "\n")

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    # Помечаем план отправленным
    plan.status = "sent"
    plan.sent_at = timezone.now()
    plan.save(update_fields=["status", "sent_at"])

    # Статус исследования — отправлено
    study.status = "sent"
    study.save(update_fields=["status"])

    return True
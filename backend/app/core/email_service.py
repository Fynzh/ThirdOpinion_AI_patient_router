"""
Отправка плана пациента по email.
"""

import mimetypes
import os

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.utils.html import escape

from .patient_registry import get_personal_data


# Ссылка для кнопки «Записаться на приём»
BOOKING_URL = "https://platform.thirdopinion.ai/"


def _build_recommendations_text(snapshot: list) -> str:
    """Плоский текст рекомендаций для text-версии письма."""
    if not snapshot:
        return "Рекомендаций нет."

    priority_map = {"high": "СРОЧНО", "medium": "Планово", "low": "Профилактически"}
    lines = []
    for i, rec in enumerate(snapshot, start=1):
        priority = priority_map.get(rec.get("priority", "medium"), "")
        lines.append(f"\n{i}. {rec['specialist'].upper()} — {priority}")
        lines.append(f"   {rec['reasoning']}")
    return "\n".join(lines)


def _build_recommendations_html(snapshot: list) -> str:
    """HTML-разметка рекомендаций для html-версии письма."""
    if not snapshot:
        return "<p>Рекомендаций нет.</p>"

    priority_map = {
        "high": ("СРОЧНО", "#dc3545"),
        "medium": ("Планово", "#fd7e14"),
        "low": ("Профилактически", "#28a745"),
    }
    blocks = []
    for i, rec in enumerate(snapshot, start=1):
        priority = rec.get("priority", "medium")
        label, color = priority_map.get(priority, ("", "#6c757d"))
        blocks.append(
            f'<div style="padding: 12px 16px; margin-bottom: 10px; '
            f'background: #f8f9fa; border-left: 4px solid {color}; border-radius: 4px;">'
            f'<div style="font-weight: 600; margin-bottom: 6px;">'
            f'{i}. {escape(rec["specialist"]).capitalize()} '
            f'<span style="color: {color};">— {label}</span></div>'
            f'<div style="color: #495057;">{escape(rec["reasoning"])}</div>'
            f'</div>'
        )
    return "".join(blocks)


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
    snapshot = plan.recommendations_snapshot or []

    # ---- Формируем блоки ----
    recommendations_text = _build_recommendations_text(snapshot)
    recommendations_html = _build_recommendations_html(snapshot)

    doctor_comment_text = ""
    doctor_comment_html = ""
    if plan.doctor_comment and plan.doctor_comment.strip():
        doctor_comment_text = (
            "\n════════════════════════════════════════\n"
            "КОММЕНТАРИЙ ВРАЧА\n"
            "════════════════════════════════════════\n"
            f"{plan.doctor_comment.strip()}\n"
        )
        doctor_comment_html = (
            '<h3 style="color: #495057; border-bottom: 1px solid #dee2e6; '
            'padding-bottom: 6px;">Комментарий врача</h3>'
            f'<p style="background: #fff3cd; padding: 12px; border-radius: 4px;">'
            f'{escape(plan.doctor_comment.strip())}</p>'
        )

    subject = f"План обращения по исследованию от {study.study_date}"

    # ============================================
    # TEXT-ВЕРСИЯ (для старых клиентов)
    # ============================================
    body_text = f"""Здравствуйте, {full_name}!

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
{doctor_comment_text}
════════════════════════════════════════
ЗАПИСАТЬСЯ НА ПРИЁМ:
{BOOKING_URL}

Или позвоните нам: {settings.CLINIC_PHONE}

С уважением,
Клиника «Третье мнение»
"""

    # ============================================
    # HTML-ВЕРСИЯ (с кнопкой)
    # ============================================
    body_html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, Helvetica, sans-serif; color: #333;
             line-height: 1.6; max-width: 640px; margin: 0 auto; padding: 20px;">

    <p>Здравствуйте, <strong>{escape(full_name)}</strong>!</p>

    <p>По результатам вашего исследования
       (<strong>{study.get_modality_display()}</strong> от {study.study_date})
       врач составил персональный план дальнейших действий.</p>

    <h3 style="color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 6px;">
        Данные пациента
    </h3>
    <table style="border-collapse: collapse;">
        <tr><td style="padding: 4px 12px 4px 0;"><strong>ФИО:</strong></td><td>{escape(full_name)}</td></tr>
        <tr><td style="padding: 4px 12px 4px 0;"><strong>Дата рождения:</strong></td><td>{escape(birth_date)}</td></tr>
        <tr><td style="padding: 4px 12px 4px 0;"><strong>Возраст:</strong></td><td>{patient.age}</td></tr>
        <tr><td style="padding: 4px 12px 4px 0;"><strong>Пол:</strong></td><td>{patient.get_sex_display()}</td></tr>
        <tr><td style="padding: 4px 12px 4px 0;"><strong>Телефон:</strong></td><td>{escape(phone)}</td></tr>
    </table>

    <h3 style="color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 6px;">
        Заключение рентгенолога
    </h3>
    <p style="background: #f8f9fa; padding: 12px; border-radius: 4px;">
        {escape(study.radiologist_conclusion)}
    </p>

    <h3 style="color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 6px;">
        Рекомендованный план
    </h3>
    {recommendations_html}

    {doctor_comment_html}

    <div style="text-align: center; margin: 36px 0;">
        <a href="{BOOKING_URL}"
           style="display: inline-block; padding: 16px 40px;
                  background: #0d6efd; color: #ffffff;
                  text-decoration: none; border-radius: 8px;
                  font-weight: 600; font-size: 17px;">
            Записаться на приём
        </a>
    </div>

    <p style="color: #6c757d; font-size: 12px; text-align: center;">
        Если кнопка не работает — перейдите по ссылке:<br>
        <a href="{BOOKING_URL}">{BOOKING_URL}</a>
    </p>

    <p style="text-align: center;">
        Или позвоните нам: <strong>{settings.CLINIC_PHONE}</strong>
    </p>

    <p style="margin-top: 30px;">С уважением,<br>Клиника «Третье мнение»</p>

</body>
</html>
"""

    # ---- Вывод в консоль для отладки ----
    print("\n" + "=" * 70)
    print("📧 ПИСЬМО ПАЦИЕНТУ")
    print(f"Кому: {email}")
    print(f"Тема: {subject}")
    print("=" * 70)
    print(body_text)
    print("=" * 70 + "\n")

    # ---- Создаём письмо ----
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    msg.attach_alternative(body_html, "text/html")

    # ---- Прикладываем файл исследования ----
    if study.file:
        try:
            study.file.open("rb")
            content = study.file.read()
            study.file.close()

            filename = os.path.basename(study.file.name)
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"

            msg.attach(filename, content, content_type)
            print(f"📎 Прикреплён файл: {filename} ({content_type})")
        except Exception as e:
            print(f"⚠️ Не удалось прикрепить файл: {e}")

    # ---- Отправляем ----
    msg.send(fail_silently=False)

    # ---- Обновляем статус ----
    plan.status = "sent"
    plan.sent_at = timezone.now()
    plan.save(update_fields=["status", "sent_at"])

    study.status = "sent"
    study.save(update_fields=["status"])

    return True
from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime

class Patient(models.Model):
    """
    Пациент — АНОНИМНЫЙ.
    Персональные данные (ФИО, дата рождения, телефон, email)
    хранятся в отдельном JSON-файле patient_registry.json.
    В БД — только код и обезличенные медицинские параметры.
    """
    SEX_CHOICES = [
        ("M", "Мужской"),
        ("F", "Женский"),
    ]

    patient_code = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Код пациента",
        help_text="Генерируется автоматически. Например: PAT-2026-A3F8B1",
    )
    age = models.PositiveIntegerField(verbose_name="Возраст")
    sex = models.CharField(
        max_length=1, choices=SEX_CHOICES, verbose_name="Пол"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.patient_code

    def save(self, *args, **kwargs):
        if not self.patient_code:
            self.patient_code = self._generate_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_code() -> str:
        """Генерирует уникальный код вида PAT-2026-A3F8B1."""
        year = datetime.now().year
        return f"PAT-{year}-{uuid.uuid4().hex[:6].upper()}"

class Study(models.Model):
    MODALITY_CHOICES = [
        ('CHEST_XRAY', 'Рентгенограмма грудной клетки'),
        ('FLG', 'ФЛГ'),
        ('CHEST_CT', 'КТ органов грудной клетки'),
        ('BRAIN_CT', 'КТ головного мозга'),
        ('MAMMO', 'Маммограмма'),
    ]
    STATUS_CHOICES = [
        ('processing', 'ИИ обрабатывает'),
        ('ai_done', 'ИИ обработал — ждёт врача'),
        ('in_review', 'Врач проверяет'),
        ('approved', 'План утверждён'),
        ('sent', 'Отправлено пациенту'),
    ]

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='studies',
        verbose_name="Пациент"
    )
    modality = models.CharField(
        max_length=20, choices=MODALITY_CHOICES, verbose_name="Тип исследования"
    )
    study_date = models.DateField(verbose_name="Дата исследования")
    radiologist_conclusion = models.TextField(
        verbose_name="Заключение рентгенолога",
        help_text="Текст, который написал врач-рентгенолог"
    )
    file = models.FileField(
        upload_to='studies/', blank=True, null=True, verbose_name="Файл"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Исследование"
        verbose_name_plural = "Исследования"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_modality_display()} — {self.patient.patient_code} ({self.study_date})"

class Recommendation(models.Model):
    SOURCE_CHOICES = [
        ('ai', 'ИИ'),
        ('doctor', 'Врач'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Ожидает проверки'),
        ('approved', 'Одобрена'),
        ('edited', 'Изменена врачом'),
        ('rejected', 'Отклонена'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'Высокий'),
        ('medium', 'Средний'),
        ('low', 'Низкий'),
    ]

    study = models.ForeignKey(
        Study, on_delete=models.CASCADE, related_name='recommendations',
        verbose_name="Исследование"
    )
    source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default='ai', verbose_name="Источник"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус"
    )
    specialist = models.CharField(max_length=100, verbose_name="Специалист")
    specialty_code = models.CharField(max_length=50, blank=True, verbose_name="Код специальности")
    reasoning = models.TextField(verbose_name="Обоснование")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет"
    )
    confidence = models.FloatField(null=True, blank=True, verbose_name="Уверенность ИИ")

    raw_model_output = models.JSONField(default=dict, blank=True)

    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Проверил врач"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Рекомендация"
        verbose_name_plural = "Рекомендации"
        ordering = ['-priority', 'specialist']

    def __str__(self):
        return f"[{self.get_source_display()}] {self.specialist} ({self.get_status_display()})"

class CarePlan(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('approved', 'Утверждён'),
        ('sent', 'Отправлен пациенту'),
    ]

    study = models.OneToOneField(
        Study, on_delete=models.CASCADE, related_name='care_plan',
        verbose_name="Исследование"
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name="Утвердил врач"
    )
    recommendations_snapshot = models.JSONField(
        default=list, verbose_name="Снимок рекомендаций"
    )
    doctor_comment = models.TextField(blank=True, verbose_name="Комментарий врача")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "План обращения"
        verbose_name_plural = "Планы обращения"

    def __str__(self):
        return f"План для {self.study.patient.patient_code} ({self.get_status_display()})"
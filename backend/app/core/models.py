from django.db import models
from django.contrib.auth.models import User
class Patient(models.Model):
    patient_code = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Анонимный код пациента",
        help_text="Например: PAT-2026-0001"
    )
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    birth_date = models.DateField(verbose_name="Дата рождения")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"

    def __str__(self):
        return self.full_name

class Study(models.Model):
    MODALITY_CHOICES = [
        ('CHEST_XRAY', 'Рентгенограмма грудной клетки'),
        ('FLG', 'ФЛГ'),
        ('CHEST_CT', 'КТ органов грудной клетки'),
        ('BRAIN_CT', 'КТ головного мозга'),
        ('MAMMO', 'Маммограмма'),
    ]
    STATUS_CHOICES = [
        ('new', 'Новое — ждёт обработки ИИ'),
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
        max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Исследование"
        verbose_name_plural = "Исследования"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_modality_display()} — {self.patient.full_name} ({self.study_date})"

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

    original_specialist = models.CharField(max_length=100, blank=True)
    original_reasoning = models.TextField(blank=True)
    original_priority = models.CharField(max_length=10, blank=True)

    doctor_comment = models.TextField(blank=True, verbose_name="Комментарий врача")
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
        return f"План для {self.study.patient.full_name} ({self.get_status_display()})"
from django.contrib import admin

from django.contrib import admin
from .models import Patient, Study, Recommendation, CarePlan


# ============================================
# РЕКОМЕНДАЦИИ — показываем ВНУТРИ исследования
# ============================================
class RecommendationInline(admin.TabularInline):
    model = Recommendation
    extra = 0  # не показывать пустые строки для добавления
    fields = (
        'source', 'specialist', 'priority', 'status',
        'reasoning', 'doctor_comment', 'confidence'
    )
    readonly_fields = ('source', 'confidence')


# ============================================
# ПАЦИЕНТ
# ============================================
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'birth_date', 'phone', 'created_at')
    search_fields = ('full_name', 'phone', 'email')
    list_filter = ('birth_date',)
    ordering = ('-created_at',)


# ============================================
# ИССЛЕДОВАНИЕ — главная карточка
# ============================================
@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'modality', 'study_date',
        'status', 'created_at'
    )
    list_filter = ('modality', 'status', 'study_date')
    search_fields = ('patient__full_name', 'radiologist_conclusion')
    inlines = [RecommendationInline]  # ← рекомендации внутри карточки
    ordering = ('-created_at',)
    actions = ['run_ai_analysis']

    fieldsets = (
        ('Пациент', {
            'fields': ('patient',)
        }),
        ('Исследование', {
            'fields': ('modality', 'study_date', 'file')
        }),
        ('Заключение рентгенолога', {
            'fields': ('radiologist_conclusion',),
            'description': 'Этот текст пойдёт в NLP-модель для анализа'
        }),
        ('Статус', {
            'fields': ('status',)
        }),
    )

    def run_ai_analysis(self, request, queryset):
        """
        Action: запустить ИИ-анализ для выбранных исследований.
        Появляется в выпадающем меню «Действие» над списком.
        """
        from nlp_module.analyzer import generate_recommendations

        count = 0
        for study in queryset:
            # Удаляем старые рекомендации от ИИ (если были)
            study.recommendations.filter(source='ai').delete()
            # Вызываем NLP-модуль
            result = generate_recommendations(
                radiologist_conclusion=study.radiologist_conclusion,
                patient_info={
                    "full_name": study.patient.full_name,
                    "birth_date": str(study.patient.birth_date),
                }
            )
            # Сохраняем рекомендации в базу
            for rec in result.get("recommendations", []):
                Recommendation.objects.create(
                    study=study,
                    source='ai',
                    status='pending',
                    specialist=rec.get("specialist", ""),
                    specialty_code=rec.get("specialty_code", ""),
                    reasoning=rec.get("reasoning", ""),
                    priority=rec.get("priority", "medium"),
                    confidence=rec.get("confidence"),
                    raw_model_output=rec,
                )

            # Обновляем статус исследования
            study.status = 'ai_done'
            study.save()
            count += 1
        self.message_user(
            request,
            f"✅ ИИ обработал {count} исследований. Рекомендации добавлены."
        )

    run_ai_analysis.short_description = "Запустить ИИ-анализ"

# ============================================
# РЕКОМЕНДАЦИЯ — отдельная карточка
# ============================================
@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'study', 'specialist', 'source',
        'priority', 'status', 'confidence'
    )
    list_filter = ('source', 'status', 'priority')
    search_fields = ('specialist', 'reasoning')
    readonly_fields = (
        'original_specialist', 'original_reasoning', 'original_priority',
        'raw_model_output', 'created_at'
    )
    ordering = ('-created_at',)


# ============================================
# ПЛАН ОБРАЩЕНИЯ
# ============================================
@admin.register(CarePlan)
class CarePlanAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'study', 'status', 'approved_by',
        'approved_at', 'sent_at'
    )
    list_filter = ('status',)
    readonly_fields = (
        'recommendations_snapshot', 'created_at',
        'approved_at', 'sent_at'
    )

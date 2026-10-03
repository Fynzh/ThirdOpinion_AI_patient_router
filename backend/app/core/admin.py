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
        """Action: запустить ИИ-анализ для выбранных исследований."""
        from nlp_module.analyzer import (
            generate_recommendations,
            RecommendationError,
        )
        from nlp_module.llm import call_llm

        ok = 0
        errors = 0
        for study in queryset:
            study.recommendations.filter(source='ai').delete()

            try:
                result = generate_recommendations(
                    radiologist_conclusion=study.radiologist_conclusion,
                    call_llm=call_llm,
                )
            except RecommendationError:
                errors += 1
                continue
            except Exception:
                errors += 1
                continue

            for rec in result.get("recommendations", []):
                Recommendation.objects.create(
                    study=study,
                    source='ai',
                    status='pending',
                    specialist=rec["specialist"],
                    specialty_code=rec["specialty_code"],
                    reasoning=rec["reasoning"],
                    priority=rec["priority"],
                    confidence=rec.get("confidence"),
                    raw_model_output=rec,
                )

            if result.get("status") == "no_findings":
                study.status = 'approved'
            else:
                study.status = 'ai_done'
            study.save()
            ok += 1

        self.message_user(
            request,
            f"✅ ИИ обработал: {ok}. Ошибок: {errors}."
        )

    run_ai_analysis.short_description = "🧠 Запустить ИИ-анализ"

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

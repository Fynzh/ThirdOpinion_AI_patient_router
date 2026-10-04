from django.contrib import admin
from django import forms
from .models import Patient, Study, Recommendation, CarePlan

def get_patient_full_name(patient_code: str) -> str:
    """Возвращает ФИО пациента из JSON-реестра. Если нет — возвращает код."""
    from .patient_registry import get_personal_data
    data = get_personal_data(patient_code) or {}
    return data.get("full_name", patient_code)
# ============================================
# РЕКОМЕНДАЦИИ — показываем ВНУТРИ исследования
# ============================================
class RecommendationInline(admin.TabularInline):
    model = Recommendation
    extra = 0  # не показывать пустые строки для добавления
    fields = (
        'source', 'specialist', 'priority', 'status',
        'reasoning', 'confidence'
    )
    readonly_fields = ('source', 'confidence')

# ============================================
# ПАЦИЕНТ — анонимный в БД, персональные данные в JSON
# ============================================
class PatientAdminForm(forms.ModelForm):
    """
    Форма пациента. Включает виртуальные поля для персональных данных,
    которые хранятся НЕ в БД, а в JSON-реестре.
    """
    full_name = forms.CharField(
        required=False, label="ФИО",
        widget=forms.TextInput(attrs={'style': 'width: 500px'}),
    )
    birth_date = forms.DateField(
        required=False, label="Дата рождения",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    phone = forms.CharField(required=False, label="Телефон")
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = Patient
        fields = ['patient_code', 'age', 'sex']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    form = PatientAdminForm
    list_display = ('patient_code', 'full_name_display', 'age', 'sex', 'created_at')
    search_fields = ('patient_code',)
    list_filter = ('sex',)
    readonly_fields = ('patient_code', 'created_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Анонимные данные (в БД)', {
            'fields': ('patient_code', 'age', 'sex'),
            'description': 'Эти поля хранятся в основной БД. Персональных данных тут нет.',
        }),
        ('Персональные данные (JSON-реестр)', {
            'fields': ('full_name', 'birth_date', 'phone', 'email'),
            'description': (
                'Эти поля хранятся ОТДЕЛЬНО от БД, в файле patient_registry.json. '
                'В основную БД они не попадают. Никто, кроме врача, их не видит.'
            ),
        }),
    )
    @admin.display(description="ФИО")
    def full_name_display(self, obj):
        return get_patient_full_name(obj.patient_code)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            from .patient_registry import get_personal_data
            data = get_personal_data(obj.patient_code) or {}
            for field in ['full_name', 'birth_date', 'phone', 'email']:
                if field in data and field in form.base_fields:
                    form.base_fields[field].initial = data[field]
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from .patient_registry import set_personal_data
        personal = {}
        for field in ['full_name', 'birth_date', 'phone', 'email']:
            value = form.cleaned_data.get(field)
            if value:
                personal[field] = value.isoformat() if hasattr(value, 'isoformat') else value
        if personal:
            set_personal_data(obj.patient_code, personal)



# ============================================
# ИССЛЕДОВАНИЕ — главная карточка
# ============================================
@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient_code_display', 'patient_full_name_display',
        'modality', 'study_date', 'status', 'created_at'
    )
    list_filter = ('modality', 'status', 'study_date')
    search_fields = ('patient__patient_code', 'radiologist_conclusion')
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Подменяет выпадающий список для поля 'patient' — показывает ФИО."""
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "patient" and field is not None:
            field.label_from_instance = self._patient_label
        return field

    @staticmethod
    def _patient_label(obj):
        """Что показывать в выпадающем списке для пациента."""
        from .patient_registry import get_personal_data
        data = get_personal_data(obj.patient_code) or {}
        full_name = data.get("full_name")
        if full_name:
            return f"{full_name} ({obj.patient_code})"
        return obj.patient_code

    @admin.display(description="Код пациента")
    def patient_code_display(self, obj):
        return obj.patient.patient_code

    @admin.display(description="ФИО пациента")
    def patient_full_name_display(self, obj):
        return get_patient_full_name(obj.patient.patient_code)

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
                    patient_age=study.patient.age,
                    patient_sex=study.patient.sex,
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
            f"🔄 Перегенерировано: {ok}. Ошибок: {errors}."
        )

    run_ai_analysis.short_description = "🔄 Перегенерировать рекомендации"

# ============================================
# РЕКОМЕНДАЦИЯ — отдельная карточка
# ============================================
@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    change_form_template = "admin/core/recommendation/change_form.html"
    list_display = (
        'id', 'study', 'patient_full_name_display',
        'specialist', 'source_display', 'priority', 'status', 'confidence'
    )
    list_filter = ('source', 'status', 'priority')
    search_fields = ('specialist', 'reasoning')
    readonly_fields = ('source', 'raw_model_output', 'created_at', 'study_conclusion_display')
    ordering = ('-created_at',)
    actions = ['approve_selected', 'reject_selected']

    fieldsets = (
        ('Основное', {
            'fields': (
                'study', 'source', 'status',
                'specialist', 'specialty_code',
                'reasoning', 'priority', 'confidence',
            ),
        }),
        ('Заключение рентгенолога (для сверки)', {
            'fields': ('study_conclusion_display',),
            'description': (
                'Оригинальный текст заключения. Сверяйте рекомендации ИИ '
                'с фактическим содержанием исследования.'
            ),
        }),
        ('Заключение врача', {
            'fields': ('reviewed_by', 'reviewed_at'),
            'description': 'Правки вносите в поле «Обоснование» выше.',
        }),
    )

    @admin.display(description="ФИО пациента")
    def patient_full_name_display(self, obj):
        return get_patient_full_name(obj.study.patient.patient_code)

    @admin.display(description="Заключение рентгенолога")
    def study_conclusion_display(self, obj):
        return obj.study.radiologist_conclusion

    # ----- Действия -----

    @admin.action(description="✅ Одобрить выбранные рекомендации")
    def approve_selected(self, request, queryset):
        from django.utils import timezone
        count = 0
        for rec in queryset:
            if rec.status == "rejected":
                continue
            rec.status = "approved"
            if request.user.is_authenticated:
                rec.reviewed_by = request.user
            rec.reviewed_at = timezone.now()
            rec.save()
            count += 1
        self.message_user(request, f"✅ Одобрено: {count}")

    @admin.action(description="❌ Отклонить выбранные рекомендации")
    def reject_selected(self, request, queryset):
        from django.utils import timezone
        count = 0
        for rec in queryset:
            rec.status = "rejected"
            if request.user.is_authenticated:
                rec.reviewed_by = request.user
            rec.reviewed_at = timezone.now()
            rec.save()
            count += 1
        self.message_user(request, f"❌ Отклонено: {count}")
    def response_change(self, request, obj):
        """
        Перехватывает нажатия наших кнопок «Одобрить» / «Отклонить».
        Срабатывает ПОСЛЕ стандартного сохранения формы.
        """
        from django.http import HttpResponseRedirect
        from django.utils import timezone

        # Нажали «Одобрить»
        if "_approve_recommendation" in request.POST:
            obj.status = "approved"
            if request.user.is_authenticated:
                obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save()
            self.message_user(
                request,
                f"✅ Рекомендация #{obj.id} одобрена.",
            )
            return HttpResponseRedirect(request.path)

        # Нажали «Отклонить»
        if "_reject_recommendation" in request.POST:
            obj.status = "rejected"
            if request.user.is_authenticated:
                obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save()
            self.message_user(
                request,
                f"❌ Рекомендация #{obj.id} отклонена.",
            )
            return HttpResponseRedirect(request.path)

        # Обычное сохранение — стандартная логика Django
        return super().response_change(request, obj)

    @admin.display(description="Источник", ordering="source")
    def source_display(self, obj):
        return obj.get_source_display()

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

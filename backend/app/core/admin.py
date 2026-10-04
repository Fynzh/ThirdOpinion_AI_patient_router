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
    extra = 0
    fields = (
        'source', 'specialist', 'priority', 'status',
        'reasoning', 'confidence'
    )
    readonly_fields = ('source', 'status', 'confidence')

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
        'display_title_short', 'modality', 'study_date',
        'slices_count', 'status', 'created_at',
    )
    list_filter = ('modality', 'status', 'study_date')
    search_fields = (
        'patient__patient_code', 'title', 'radiologist_conclusion',
    )
    inlines = [RecommendationInline]  # ← рекомендации внутри карточки
    ordering = ('-created_at',)
    actions = ['run_ai_analysis']
    readonly_fields = ('status',)

    fieldsets = (
        ('Пациент', {
            'fields': ('patient',)
        }),
        ('Исследование', {
            'fields': ('modality', 'title', 'study_date', 'slices_count', 'file'),
            'description': (
                'Название — краткая суть («Очаг в легком», «Коронарный кальциноз»). '
                'Если не указать — система возьмёт первую строку заключения. '
                'Срезы — только для КТ/МРТ.'
            ),
        }),
        ('Заключение платформы «Третье Мнение»', {
            'fields': ('radiologist_conclusion',),
            'description': 'Этот текст пойдёт в NLP-модель для анализа'
        }),
        ('Текущий статус', {
            'fields': ('status',),
            'description': (
                'Статус меняется автоматически: '
                'processing — ИИ обрабатывает, '
                'ai_done — ИИ ответил, ждёт врача, '
                'approved — план утверждён, '
                'sent — отправлен пациенту.'
            ),
        }),
    )

    @admin.display(description="Название", ordering="title")
    def display_title_short(self, obj):
        """Обрезанное название для колонки списка."""
        text = obj.display_title
        return text[:50] + ("…" if len(text) > 50 else "")

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
    readonly_fields = (
        'source', 'status', 'reviewed_by_display',
        'raw_model_output', 'created_at', 'study_conclusion_display',
    )
    ordering = ('-created_at',)
    actions = ['approve_selected', 'reject_selected']

    fieldsets = (
        ('Основное', {
            'fields': (
                'study', 'source',
                'specialist', 'specialty_code',
                'reasoning', 'priority', 'confidence',
            ),
        }),
        ('Текущий статус', {
            'fields': ('status',),
            'description': (
                'Статус меняется автоматически: '
                'pending — ждёт проверки, '
                'approved — одобрена кнопкой, '
                'rejected — отклонена кнопкой.'
            ),
        }),
        ('Заключение платформы «Третье Мнение» (для сверки)', {
            'fields': ('study_conclusion_display',),
            'description': (
                'Оригинальный текст заключения платформы. Сверяйте '
                'рекомендации ИИ с фактическим содержанием исследования.'
            ),
        }),
        ('Заключение врача', {
            'fields': ('reviewed_by_display', 'reviewed_at'),
            'description': 'Правки вносите в поле «Обоснование» выше.',
        }),
    )

    @admin.display(description="Проверил")
    def reviewed_by_display(self, obj):
        """Показывает логин врача, который проверил рекомендацию. Только чтение."""
        if obj.reviewed_by:
            return obj.reviewed_by.username
        return "— (ещё не проверено)"

    @admin.display(description="ФИО пациента")
    def patient_full_name_display(self, obj):
        return get_patient_full_name(obj.study.patient.patient_code)

    @admin.display(description='Заключение платформы «Третье Мнение»')
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
    change_form_template = "admin/core/careplan/change_form.html"
    list_display = (
        'id', 'study', 'patient_full_name_display',
        'status', 'created_at', 'sent_at',
    )
    list_filter = ('status',)
    readonly_fields = (
        'study', 'recommendations_display',
        'status', 'created_at', 'updated_at', 'sent_at',
        'patient_info_display', 'study_conclusion_display',
        'study_file_display',
    )
    fieldsets = (
        ('Пациент', {
            'fields': ('patient_info_display',),
        }),
        ('Исследование', {
            'fields': ('study', 'study_conclusion_display'),
        }),
        ('Рекомендованный план', {
            'fields': ('recommendations_display',),
            'description': (
                'Одобренные врачом рекомендации. '
                'Список обновляется автоматически при изменении рекомендаций.'
            ),
        }),
        ('Комментарий врача', {
            'fields': ('doctor_comment',),
        }),
        ('Статус', {
            'fields': ('status', 'created_at', 'updated_at', 'sent_at'),
        }),
    )

    @admin.display(description="Рекомендации")
    def recommendations_display(self, obj):
        """Красиво форматирует список рекомендаций для админки."""
        from django.utils.html import format_html, format_html_join
        from django.utils.safestring import mark_safe

        if not obj.recommendations_snapshot:
            return mark_safe(
                '<p style="color:#6c757d;font-style:italic;">'
                'Пока нет одобренных рекомендаций.</p>'
            )

        priority_labels = {
            "high": ("🔴 СРОЧНО", "#dc3545"),
            "medium": ("🟡 Планово", "#fd7e14"),
            "low": ("🟢 Профилактически", "#28a745"),
        }

        blocks = []
        for i, rec in enumerate(obj.recommendations_snapshot, start=1):
            specialist = (rec.get("specialist") or "—").capitalize()
            reasoning = rec.get("reasoning") or "—"
            priority = rec.get("priority", "medium")
            label, color = priority_labels.get(priority, ("—", "#6c757d"))

            block = format_html(
                '<div style="'
                'padding: 12px 16px; margin-bottom: 10px;'
                'background: #f8f9fa; border-left: 4px solid {color};'
                'border-radius: 4px;">'
                '<div style="font-weight: 600; margin-bottom: 6px;">'
                '{num}. {spec} <span style="color: {color};">— {label}</span>'
                '</div>'
                '<div style="color: #495057; line-height: 1.5;">{reasoning}</div>'
                '</div>',
                color=color,
                num=i,
                spec=specialist,
                label=label,
                reasoning=reasoning,
            )
            blocks.append(block)

        return mark_safe("".join(blocks))

    @admin.display(description="ФИО пациента")
    def patient_full_name_display(self, obj):
        return get_patient_full_name(obj.study.patient.patient_code)

    @admin.display(description="Файл исследования")
    def study_file_display(self, obj):
        """Ссылка на скачивание файла исследования."""
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe

        file = obj.study.file
        if not file:
            return mark_safe(
                '<span style="color:#6c757d;font-style:italic;">'
                '— файл не прикреплён</span>'
            )
        return format_html(
            '<a href="{}" target="_blank" '
            'style="display: inline-block; padding: 6px 12px; '
            'background: #0d6efd; color: white; '
            'border-radius: 4px; text-decoration: none;">'
            '📎 Скачать файл'
            '</a>',
            file.url,
        )

    @admin.display(description="Данные пациента")
    def patient_info_display(self, obj):
        from .patient_registry import get_personal_data
        code = obj.study.patient.patient_code
        data = get_personal_data(code) or {}
        patient = obj.study.patient
        return (
            f"Код: {code}\n"
            f"ФИО: {data.get('full_name', '—')}\n"
            f"Дата рождения: {data.get('birth_date', '—')}\n"
            f"Возраст: {patient.age}\n"
            f"Пол: {patient.get_sex_display()}\n"
            f"Телефон: {data.get('phone', '—')}\n"
            f"Email: {data.get('email', '—')}"
        )

    @admin.display(description='Заключение платформы «Третье Мнение»')
    def study_conclusion_display(self, obj):
        return obj.study.radiologist_conclusion

    def response_change(self, request, obj):
        """Перехватываем кнопку «Отправить пациенту»."""
        from django.http import HttpResponseRedirect
        from .email_service import send_care_plan_email

        if "_send_care_plan" in request.POST:
            if obj.status == "sent":
                self.message_user(
                    request,
                    "⚠️ План уже был отправлен.",
                    level="WARNING",
                )
                return HttpResponseRedirect(request.path)

            success = send_care_plan_email(obj)
            if success:
                self.message_user(
                    request,
                    f"📧 План отправлен пациенту. Статус — «Отправлено».",
                )
            else:
                self.message_user(
                    request,
                    "❌ Не удалось отправить: у пациента нет email в реестре.",
                    level="ERROR",
                )
            return HttpResponseRedirect(request.path)

        return super().response_change(request, obj)

from rest_framework import serializers
from .models import Patient, Study, Recommendation, CarePlan


# ============================================
# 1. ПАЦИЕНТ (АНОНИМНЫЙ)
# ============================================
class PatientSerializer(serializers.ModelSerializer):
    """
    Переводчик для пациента.
    Отдаёт код + ФИО (для врача). Персональные данные в БД не хранятся,
    ФИО подтягивается из JSON-реестра.
    """
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    birth_date = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ('id', 'patient_code', 'age', 'sex',
                  'full_name', 'birth_date', 'phone', 'email')

    def _registry(self, obj):
        from .patient_registry import get_personal_data
        return get_personal_data(obj.patient_code) or {}

    def get_full_name(self, obj):
        return self._registry(obj).get('full_name', '')

    def get_birth_date(self, obj):
        return self._registry(obj).get('birth_date', '')

    def get_phone(self, obj):
        return self._registry(obj).get('phone', '')

    def get_email(self, obj):
        return self._registry(obj).get('email', '')


# ============================================
# 2. РЕКОМЕНДАЦИЯ
# ============================================
class RecommendationSerializer(serializers.ModelSerializer):
    """Переводчик для рекомендации."""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    source_display = serializers.CharField(
        source='get_source_display', read_only=True
    )
    study_conclusion = serializers.CharField(
        source='study.radiologist_conclusion', read_only=True
    )

    class Meta:
        model = Recommendation
        fields = '__all__'
        read_only_fields = (
            'source',
            'raw_model_output',
            'created_at',
        )


# ============================================
# 3. ИССЛЕДОВАНИЕ — ДЛЯ СПИСКА (кратко)
# ============================================
class StudyListSerializer(serializers.ModelSerializer):
    """Облегчённый переводчик для СПИСКА исследований."""
    patient_code = serializers.CharField(
        source='patient.patient_code', read_only=True
    )
    patient_full_name = serializers.SerializerMethodField()
    display_title = serializers.CharField(read_only=True)
    modality_display = serializers.CharField(
        source='get_modality_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    recommendations_count = serializers.IntegerField(
        source='recommendations.count', read_only=True
    )
    # ↓ НОВОЕ ↓
    has_draft_plan = serializers.SerializerMethodField()
    has_sent_plan = serializers.SerializerMethodField()

    class Meta:
        model = Study
        fields = (
            'id', 'patient', 'patient_code', 'patient_full_name',
            'display_title', 'title', 'modality', 'modality_display',
            'study_date', 'slices_count', 'status', 'status_display',
            'recommendations_count', 'created_at',
        )

    def get_patient_full_name(self, obj):
        from .patient_registry import get_personal_data
        data = get_personal_data(obj.patient.patient_code) or {}
        return data.get('full_name', obj.patient.patient_code)


# ============================================
# 4. ИССЛЕДОВАНИЕ — ДЛЯ КАРТОЧКИ (подробно)
# ============================================
class StudyDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    recommendations = RecommendationSerializer(many=True, read_only=True)
    care_plan = serializers.SerializerMethodField()
    modality_display = serializers.CharField(
        source='get_modality_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = Study
        fields = '__all__'

    def get_care_plan(self, obj):
        """
        Возвращает актуальный план обращения:
        - draft-план, если он есть (врач с ним работает);
        - иначе последний sent-план (для просмотра);
        - иначе None.
        """
        plan = obj.care_plans.filter(status='draft').first()
        if plan is None:
            plan = obj.care_plans.filter(status='sent').order_by('-sent_at').first()
        if plan is None:
            return None
        return CarePlanSerializer(plan).data


# ============================================
# 5. ПЛАН ОБРАЩЕНИЯ
# ============================================
class CarePlanSerializer(serializers.ModelSerializer):
    """Переводчик для плана обращения."""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = CarePlan
        fields = '__all__'
        read_only_fields = (
            'study',
            'recommendations_snapshot',
            'status',
            'created_at',
            'updated_at',
            'sent_at',
        )

class StudyCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и редактирования исследования.
    Поддерживает загрузку файла через multipart/form-data.
    """
    class Meta:
        model = Study
        fields = (
            'id',
            'patient',
            'modality',
            'title',
            'study_date',
            'slices_count',
            'radiologist_conclusion',
            'file',
            'status',
        )
        read_only_fields = ('status',)   # статус меняется автоматически


class PatientCreateSerializer(serializers.Serializer):
    """
                Сериализатор для создания пациента.
                Принимает и анонимные поля, и персональные (пойдут в JSON-реестр).
                """
    age = serializers.IntegerField(min_value=0, max_value=150)
    sex = serializers.ChoiceField(choices=['M', 'F'])
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

class PatientUpdateSerializer(serializers.Serializer):
    """Частичное обновление пациента."""
    age = serializers.IntegerField(min_value=0, max_value=150, required=False)
    sex = serializers.ChoiceField(choices=['M', 'F'], required=False)
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
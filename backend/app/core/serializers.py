from rest_framework import serializers
from .models import Patient, Study, Recommendation, CarePlan


# ============================================
# 1. ПАЦИЕНТ (АНОНИМНЫЙ)
# ============================================
class PatientAnonymizedSerializer(serializers.ModelSerializer):
    """
    Переводчик для пациента в АНОНИМНОМ виде.
    Отдаём только ID и анонимный код.
    НИКАКИХ ФИО, дат рождения, телефонов, email.
    """

    class Meta:
        model = Patient
        fields = ('id', 'patient_code')


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

    class Meta:
        model = Recommendation
        fields = '__all__'
        read_only_fields = (
            'source',
            'original_specialist',
            'original_reasoning',
            'original_priority',
            'raw_model_output',
            'created_at',
        )


# ============================================
# 3. ИССЛЕДОВАНИЕ — ДЛЯ СПИСКА (кратко)
# ============================================
class StudyListSerializer(serializers.ModelSerializer):
    """
    Облегчённый переводчик для СПИСКА исследований.
    Никаких рекомендаций и заключения — только для таблицы.
    """
    patient_code = serializers.CharField(
        source='patient.patient_code', read_only=True
    )
    modality_display = serializers.CharField(
        source='get_modality_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    recommendations_count = serializers.IntegerField(
        source='recommendations.count', read_only=True
    )

    class Meta:
        model = Study
        fields = (
            'id',
            'patient',  # ID пациента (для связи)
            'patient_code',  # анонимный код
            'modality',
            'modality_display',
            'study_date',
            'status',
            'status_display',
            'recommendations_count',
            'created_at',
        )


# ============================================
# 4. ИССЛЕДОВАНИЕ — ДЛЯ КАРТОЧКИ (подробно)
# ============================================
class StudyDetailSerializer(serializers.ModelSerializer):
    """
    Полный переводчик для ОДНОГО исследования.
    Включает пациента (анонимно) и все рекомендации.
    """
    patient = PatientAnonymizedSerializer(read_only=True)
    recommendations = RecommendationSerializer(many=True, read_only=True)
    modality_display = serializers.CharField(
        source='get_modality_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = Study
        fields = '__all__'


# ============================================
# 5. ПЛАН ОБРАЩЕНИЯ
# ============================================
class CarePlanSerializer(serializers.ModelSerializer):
    """Переводчик для финального плана."""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = CarePlan
        fields = '__all__'
        read_only_fields = (
            'recommendations_snapshot',
            'created_at',
            'approved_at',
            'sent_at',
        )
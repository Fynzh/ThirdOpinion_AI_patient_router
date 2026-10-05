from rest_framework.generics import ListAPIView, RetrieveAPIView
from .patient_registry import get_personal_data, set_personal_data, update_personal_data
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .models import Study, Recommendation, CarePlan, Patient
from .serializers import (
    StudyListSerializer, StudyDetailSerializer,
    RecommendationSerializer, CarePlanSerializer,
    StudyCreateUpdateSerializer,
    PatientSerializer,
    PatientCreateSerializer,
    PatientUpdateSerializer,
)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

# ============================================
# 1. СПИСОК + СОЗДАНИЕ ИССЛЕДОВАНИЙ
# ============================================
class StudyListCreateView(APIView):
    """
    GET  /api/studies/     — список исследований
    POST /api/studies/     — создание (multipart, с файлом)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        queryset = (
            Study.objects
            .select_related('patient')
            .prefetch_related('care_plans')
            .filter(patient__created_by=request.user)    # ← ТОЛЬКО СВОИ
            .order_by('-created_at')
        )
        serializer = StudyListSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        # 1. Проверяем, что пациент принадлежит текущему врачу
        patient_id = request.data.get("patient")
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id, created_by=request.user)
            except Patient.DoesNotExist:
                return Response(
                    {"error": "Пациент не найден или не принадлежит вам",
                     "code": "PATIENT_NOT_FOUND"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # 2. Создаём исследование
        serializer = StudyCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Некорректные данные",
                 "code": "VALIDATION_ERROR",
                 "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        study = serializer.save()
        study.refresh_from_db()

        return Response(
            StudyDetailSerializer(study).data,
            status=status.HTTP_201_CREATED,
        )

class StudyDetailView(RetrieveAPIView):
    serializer_class = StudyDetailSerializer

    def get_queryset(self):
        return (
            Study.objects
            .select_related('patient')
            .prefetch_related('recommendations', 'care_plans')
            .filter(patient__created_by=self.request.user)    # ← ТОЛЬКО СВОИ
        )


class GenerateRecommendationsView(APIView):
    """
    POST /api/studies/{id}/generate/
    Запускает NLP-анализ заключения платформы «Третье Мнение».
    """
    def post(self, request, pk):
        try:
            study = Study.objects.get(id=pk, patient__created_by=request.user)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Удаляем старые рекомендации от ИИ (если были)
        study.recommendations.filter(source='ai').delete()

        # Импорт внутри метода — чтобы Django не падал, если NLP-модуль
        # недоступен, но остальные views работают
        from nlp_module.analyzer import (
            generate_recommendations,
            RecommendationError,
        )
        from nlp_module.llm import call_llm

        # 1. Вызываем NLP-модуль
        try:
            result = generate_recommendations(
                radiologist_conclusion=study.radiologist_conclusion,
                call_llm=call_llm,
                patient_age=study.patient.age,
                patient_sex=study.patient.sex,
            )
        except RecommendationError as e:
            return Response(
                {
                    "error": f"Модель вернула неразбираемый ответ: {e}",
                    "code": "NLP_PARSE_ERROR",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка NLP-модуля: {e}", "code": "NLP_ERROR"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 2. Сохраняем рекомендации (данные уже валидированы analyzer.py)
        created = []
        for rec in result.get("recommendations", []):
            recommendation = Recommendation.objects.create(
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
            created.append(recommendation)

        # 3. Меняем статус исследования в зависимости от вердикта ИИ
        ai_status = result.get("status", "findings")
        if ai_status == "no_findings":
            # Сразу «утверждаем» — врачу нечего ревьюить
            study.status = 'approved'
        else:
            study.status = 'ai_done'
        study.save()

        # 4. Отдаём ответ фронтенду
        return Response({
            "study_id": study.id,
            "status": study.status,
            "ai_status": ai_status,
            "recommendations": RecommendationSerializer(created, many=True).data,
            "summary": result.get("summary", ""),
        })

# ============================================
# 4. РЕДАКТИРОВАНИЕ РЕКОМЕНДАЦИИ (без одобрения)
# ============================================
class EditRecommendationView(APIView):
    """
    PATCH /api/recommendations/{id}/edit/
    Врач меняет поля рекомендации. Статус автоматически становится 'edited'.
    """
    def patch(self, request, pk):
        try:
            rec = Recommendation.objects.get(
                id=pk,
                study__patient__created_by=request.user,
            )
        except Recommendation.DoesNotExist:
            return Response(
                {"error": "Рекомендация не найдена", "code": "RECOMMENDATION_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Меняем только те поля, что прислал фронт
        specialist = request.data.get("specialist")
        if specialist and specialist.strip():
            rec.specialist = specialist.strip()

        reasoning = request.data.get("reasoning")
        if reasoning and reasoning.strip():
            rec.reasoning = reasoning.strip()

        priority = request.data.get("priority")
        if priority in ["high", "medium", "low"]:
            rec.priority = priority

        if request.user.is_authenticated:
            rec.reviewed_by = request.user
        rec.reviewed_at = timezone.now()

        # save() — сигнал pre_save автоматически поставит 'edited',
        # если реально что-то изменилось
        rec.save()

        return Response(RecommendationSerializer(rec).data)


# ============================================
# 5. ОДОБРИТЬ РЕКОМЕНДАЦИЮ
# ============================================
class ApproveRecommendationView(APIView):
    """
    POST /api/recommendations/{id}/approve/
    Врач одобряет рекомендацию (без изменений или после редактирования).
    """
    def post(self, request, pk):
        try:
            rec = Recommendation.objects.get(
                id=pk,
                study__patient__created_by=request.user,
            )
        except Recommendation.DoesNotExist:
            return Response(
                {"error": "Рекомендация не найдена", "code": "RECOMMENDATION_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        rec.status = "approved"
        if request.user.is_authenticated:
            rec.reviewed_by = request.user
        rec.reviewed_at = timezone.now()
        rec.save()

        return Response(RecommendationSerializer(rec).data)


# ============================================
# 6. ОТКЛОНИТЬ РЕКОМЕНДАЦИЮ
# ============================================
class RejectRecommendationView(APIView):
    """
    POST /api/recommendations/{id}/reject/
    Врач отклоняет рекомендацию.
    """
    def post(self, request, pk):
        try:
            rec = Recommendation.objects.get(
                id=pk,
                study__patient__created_by=request.user,
            )
        except Recommendation.DoesNotExist:
            return Response(
                {"error": "Рекомендация не найдена", "code": "RECOMMENDATION_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        rec.status = "rejected"
        if request.user.is_authenticated:
            rec.reviewed_by = request.user
        rec.reviewed_at = timezone.now()
        rec.save()

        return Response(RecommendationSerializer(rec).data)


class AddDoctorRecommendationView(APIView):
    """
    POST /api/studies/{id}/add-recommendation/
    Врач добавляет свою рекомендацию.
    """
    def post(self, request, pk):
        try:
            study = Study.objects.get(id=pk, patient__created_by=request.user)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        specialist = request.data.get("specialist", "").strip()
        reasoning = request.data.get("reasoning", "").strip()

        if not specialist or not reasoning:
            return Response(
                {"error": "Поля specialist и reasoning обязательны",
                 "code": "VALIDATION_ERROR"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        priority = request.data.get("priority", "medium")
        if priority not in ["high", "medium", "low"]:
            priority = "medium"

        rec = Recommendation.objects.create(
            study=study,
            source="doctor",
            status="approved",
            specialist=specialist,
            specialty_code="",
            reasoning=reasoning,
            priority=priority,
            reviewed_at=timezone.now(),
            reviewed_by=request.user if request.user.is_authenticated else None,
        )

        return Response(
            RecommendationSerializer(rec).data,
            status=status.HTTP_201_CREATED,
        )

# ============================================
# 7. РЕДАКТИРОВАТЬ КОММЕНТАРИЙ ВРАЧА В ПЛАНЕ
# ============================================
class UpdateCarePlanCommentView(APIView):
    """
    PATCH /api/studies/{id}/care-plan/
    Body: {"doctor_comment": "..."}
    Обновляет комментарий врача в DRAFT-плане исследования.
    Если плана нет или он уже sent — 400.
    """
    def patch(self, request, pk):
        # 1. Достаём исследование
        try:
            study = Study.objects.get(id=pk, patient__created_by=request.user)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Ищем draft-план
        plan = study.care_plans.filter(status='draft').first()
        if plan is None:
            # Может, есть sent — но его редактировать нельзя
            sent_exists = study.care_plans.filter(status='sent').exists()
            if sent_exists:
                return Response(
                    {
                        "error": "План уже отправлен пациенту. Правки невозможны.",
                        "code": "PLAN_ALREADY_SENT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "error": "Черновик плана ещё не создан. "
                             "Одобрьте хотя бы одну рекомендацию.",
                    "code": "NO_DRAFT_PLAN",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Обновляем только doctor_comment
        if "doctor_comment" not in request.data:
            return Response(
                {
                    "error": "Поле doctor_comment обязательно",
                    "code": "VALIDATION_ERROR",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        plan.doctor_comment = request.data.get("doctor_comment", "")
        plan.save(update_fields=["doctor_comment", "updated_at"])

        return Response(CarePlanSerializer(plan).data)


# ============================================
# 8. ОТПРАВИТЬ ПЛАН ПАЦИЕНТУ
# ============================================
class SendCarePlanView(APIView):
    """
    POST /api/studies/{id}/send/
    Отправляет план пациенту на email.
    Работает только с DRAFT-планом.
    """
    def post(self, request, pk):
        # 1. Достаём исследование
        try:
            study = Study.objects.get(id=pk, patient__created_by=request.user)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Ищем draft-план
        plan = study.care_plans.filter(status='draft').first()
        if plan is None:
            sent_exists = study.care_plans.filter(status='sent').exists()
            if sent_exists:
                return Response(
                    {
                        "error": "План уже был отправлен ранее.",
                        "code": "PLAN_ALREADY_SENT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "error": "Нет черновика плана для отправки.",
                    "code": "NO_DRAFT_PLAN",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Проверяем, что есть email пациента
        personal = get_personal_data(study.patient.patient_code) or {}
        if not personal.get("email"):
            return Response(
                {
                    "error": "У пациента не указан email. "
                             "Добавьте email в карточке пациента.",
                    "code": "NO_PATIENT_EMAIL",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Отправляем письмо
        from .email_service import send_care_plan_email
        try:
            success = send_care_plan_email(plan)
        except Exception as e:
            return Response(
                {"error": f"Ошибка отправки: {e}", "code": "EMAIL_SEND_ERROR"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not success:
            return Response(
                {
                    "error": "Не удалось отправить: email не найден в реестре.",
                    "code": "NO_PATIENT_EMAIL",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5. Возвращаем обновлённый план
        plan.refresh_from_db()
        return Response(
            {
                "success": True,
                "message": "План отправлен пациенту.",
                "plan": CarePlanSerializer(plan).data,
            }
        )


# ============================================
# 10. РЕДАКТИРОВАНИЕ ИССЛЕДОВАНИЯ
# ============================================
class StudyUpdateView(APIView):
    """
    PATCH /api/studies/{id}/
    Частичное обновление исследования.
    Можно менять всё, кроме status.
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, pk):
        try:
            study = Study.objects.get(id=pk, patient__created_by=request.user)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudyCreateUpdateSerializer(
            study, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                {
                    "error": "Некорректные данные",
                    "code": "VALIDATION_ERROR",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        study.refresh_from_db()

        return Response(StudyDetailSerializer(study).data)


# ============================================
# 11. ЗАГРУЗКА / ЗАМЕНА ФАЙЛА
# ============================================
class StudyUploadFileView(APIView):
    """
    POST /api/studies/{id}/upload-file/
    Content-Type: multipart/form-data
    Body: file=<файл>
    Загружает или заменяет файл исследования.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            study = Study.objects.get(id=pk, patient__created_by=request.user)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response(
                {"error": "Файл не передан. Используйте поле 'file'.",
                 "code": "FILE_REQUIRED"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ограничение размера — 50 МБ (Gmail всё равно 25 МБ пропустит)
        if uploaded.size > 50 * 1024 * 1024:
            return Response(
                {"error": "Файл больше 50 МБ", "code": "FILE_TOO_LARGE"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        study.file = uploaded
        study.save(update_fields=["file", "updated_at"])

        return Response(
            {
                "success": True,
                "file_endpoint": (
                    f"/api/studies/{study.id}/file/" if study.file else None
                ),
                "file_name": (
                    study.file.name.split("/")[-1] if study.file else None
                ),
            }
        )


# ============================================
# 12. СКАЧИВАНИЕ ФАЙЛА (с проверкой прав)
# ============================================
class StudyDownloadFileView(APIView):
    """
    GET /api/studies/{id}/file/
    Отдаёт файл исследования. Требует токен.
    """
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication,
    ]
    def get(self, request, pk):
        try:
            study = Study.objects.get(id=pk, patient__created_by=request.user)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not study.file:
            return Response(
                {"error": "У исследования нет файла", "code": "FILE_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        from django.http import FileResponse
        import os

        try:
            study.file.open("rb")
            response = FileResponse(
                study.file,
                as_attachment=True,
                filename=os.path.basename(study.file.name),
            )
            return response
        except FileNotFoundError:
            return Response(
                {"error": "Файл потерян на диске", "code": "FILE_MISSING"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# ============================================
# 13. СПИСОК И СОЗДАНИЕ ПАЦИЕНТОВ
# ============================================
class PatientListCreateView(APIView):
    """
    GET  /api/patients/   — список пациентов
    POST /api/patients/   — создать пациента
    """
    def get(self, request):
        patients = (
            Patient.objects
            .filter(created_by=request.user)      # ← ТОЛЬКО СВОИ
            .order_by('-created_at')
        )
        return Response(PatientSerializer(patients, many=True).data)

    def post(self, request):
        serializer = PatientCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Некорректные данные",
                 "code": "VALIDATION_ERROR",
                 "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # 1. Создаём анонимного пациента (в БД)
        patient = Patient.objects.create(
            age=data["age"],
            sex=data["sex"],
            created_by=request.user,             # ← ВЛАДЕЛЕЦ
        )

        # 2. Сохраняем персональные данные в JSON-реестр
        personal = {}
        for field in ["full_name", "birth_date", "phone", "email"]:
            value = data.get(field)
            if value:
                personal[field] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
        if personal:
            set_personal_data(patient.patient_code, personal)

        return Response(
            PatientSerializer(patient).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================
# 14. ДЕТАЛИ И ОБНОВЛЕНИЕ ПАЦИЕНТА
# ============================================
class PatientDetailView(APIView):
    """
    GET    /api/patients/{id}/  — детали
    PATCH  /api/patients/{id}/  — обновить
    """
    def get(self, request, pk):
        try:
            patient = Patient.objects.get(id=pk, created_by=request.user)
        except Patient.DoesNotExist:
            return Response(
                {"error": "Пациент не найден", "code": "PATIENT_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PatientSerializer(patient).data)

    def patch(self, request, pk):
        try:
            patient = Patient.objects.get(id=pk, created_by=request.user)
        except Patient.DoesNotExist:
            return Response(
                {"error": "Пациент не найден", "code": "PATIENT_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PatientUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error": "Некорректные данные",
                 "code": "VALIDATION_ERROR",
                 "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # 1. Обновляем анонимные поля в БД
        if "age" in data:
            patient.age = data["age"]
        if "sex" in data:
            patient.sex = data["sex"]
        patient.save()

        # 2. Обновляем персональные в JSON-реестре
        personal = {}
        for field in ["full_name", "birth_date", "phone", "email"]:
            if field in data:
                value = data[field]
                personal[field] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
        if personal:
            update_personal_data(patient.patient_code, **personal)

        return Response(PatientSerializer(patient).data)

# ============================================
# 15. ДОСТУПНЫЕ ИССЛЕДОВАНИЯ ПАЦИЕНТА
# ============================================
class PatientAvailableStudiesView(APIView):
    """
    GET /api/patients/{id}/available-studies/
    Возвращает список исследований пациента.
    Query-параметры (опционально):
        ?status=sent|draft|ai_done  — фильтр по статусу исследования
        ?has_plan=false             — только те, у которых нет плана
    """
    def get(self, request, pk):
        try:
            patient = Patient.objects.get(id=pk, created_by=request.user)
        except Patient.DoesNotExist:
            return Response(
                {"error": "Пациент не найден", "code": "PATIENT_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        studies = (
            patient.studies
            .select_related('patient')
            .prefetch_related('care_plans', 'recommendations')
            .order_by('-created_at')
        )

        # Фильтр по статусу исследования
        status_filter = request.query_params.get('status')
        if status_filter:
            studies = studies.filter(status=status_filter)

        # Фильтр «нет плана вообще»
        has_plan = request.query_params.get('has_plan')
        if has_plan == 'false':
            studies = studies.filter(care_plans__isnull=True)
        elif has_plan == 'true':
            studies = studies.filter(care_plans__isnull=False).distinct()

        serializer = StudyListSerializer(studies, many=True)
        return Response(serializer.data)
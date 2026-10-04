from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Study, Recommendation, CarePlan
from .serializers import (
    StudyListSerializer, StudyDetailSerializer,
    RecommendationSerializer, CarePlanSerializer,
)

class StudyListView(ListAPIView):
    """
    GET /api/studies/
    Отдаёт список всех исследований (кратко).
    """
    queryset = Study.objects.select_related('patient').all()
    serializer_class = StudyListSerializer

class StudyDetailView(RetrieveAPIView):
    """
    GET /api/studies/{id}/
    Отдаёт полную карточку одного исследования.
    Включает пациента (анонимно) и все рекомендации.
    """
    queryset = Study.objects.select_related('patient').prefetch_related('recommendations')
    serializer_class = StudyDetailSerializer


class GenerateRecommendationsView(APIView):
    """
    POST /api/studies/{id}/generate/
    Запускает NLP-анализ заключения платформы «Третье Мнение».
    """
    def post(self, request, pk):
        try:
            study = Study.objects.get(id=pk)
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
            rec = Recommendation.objects.get(id=pk)
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
            rec = Recommendation.objects.get(id=pk)
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
            rec = Recommendation.objects.get(id=pk)
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
            study = Study.objects.get(id=pk)
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
            study = Study.objects.get(id=pk)
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
            study = Study.objects.get(id=pk)
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
        from .patient_registry import get_personal_data
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
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
    Запускает NLP-анализ заключения рентгенолога.
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

class ReviewRecommendationView(APIView):
    """
    PATCH /api/recommendations/{id}/review/
    Врач одобряет, изменяет или отклоняет рекомендацию.
    """
    def patch(self, request, pk):
        try:
            rec = Recommendation.objects.get(id=pk)
        except Recommendation.DoesNotExist:
            return Response(
                {"error": "Рекомендация не найдена", "code": "RECOMMENDATION_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        decision = request.data.get("decision")
        if decision not in ["approved", "edited", "rejected"]:
            return Response(
                {"error": "decision должен быть approved, edited или rejected",
                 "code": "VALIDATION_ERROR"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Сохраняем оригинал при первом редактировании
        if rec.source == "ai" and not rec.original_specialist:
            rec.original_specialist = rec.specialist
            rec.original_reasoning = rec.reasoning
            rec.original_priority = rec.priority

        # Применяем изменения, если врач изменил
        if decision == "edited":
            specialist = request.data.get("specialist")
            if specialist:
                rec.specialist = specialist
            reasoning = request.data.get("reasoning")
            if reasoning:
                rec.reasoning = reasoning
            priority = request.data.get("priority")
            if priority in ["high", "medium", "low"]:
                rec.priority = priority

        # Обновляем статус и метаданные
        rec.status = decision
        rec.doctor_comment = request.data.get("doctor_comment", "")
        rec.reviewed_at = timezone.now()
        if request.user.is_authenticated:
            rec.reviewed_by = request.user
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
            doctor_comment=request.data.get("doctor_comment", ""),
            reviewed_at=timezone.now(),
            reviewed_by=request.user if request.user.is_authenticated else None,
        )

        return Response(
            RecommendationSerializer(rec).data,
            status=status.HTTP_201_CREATED,
        )

class FinalizePlanView(APIView):
    """
    POST /api/studies/{id}/finalize/
    Собирает approved + edited рекомендации и создаёт CarePlan.
    """
    def post(self, request, pk):
        try:
            study = Study.objects.get(id=pk)
        except Study.DoesNotExist:
            return Response(
                {"error": "Исследование не найдено", "code": "STUDY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        final_recs = study.recommendations.filter(
            status__in=["approved", "edited"]
        ).values(
            "id", "specialist", "specialty_code", "reasoning",
            "priority", "source", "status"
        )

        if not final_recs.exists():
            return Response(
                {"error": "Нет одобренных рекомендаций для утверждения",
                 "code": "NO_APPROVED_RECOMMENDATIONS"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plan, _ = CarePlan.objects.update_or_create(
            study=study,
            defaults={
                "approved_by": request.user if request.user.is_authenticated else None,
                "recommendations_snapshot": list(final_recs),
                "doctor_comment": request.data.get("doctor_comment", ""),
                "status": "approved",
                "approved_at": timezone.now(),
            },
        )

        study.status = "approved"
        study.save()

        return Response(CarePlanSerializer(plan).data)
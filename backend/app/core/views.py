from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Study, Recommendation
from .serializers import (
    StudyListSerializer, StudyDetailSerializer,
    RecommendationSerializer,
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
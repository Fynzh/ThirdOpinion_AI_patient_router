from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Study
from .serializers import StudyListSerializer, StudyDetailSerializer


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
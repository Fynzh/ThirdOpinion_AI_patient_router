from django.urls import path
from .views import (
    StudyListView,
    StudyDetailView,
    GenerateRecommendationsView,
    ReviewRecommendationView,
    AddDoctorRecommendationView,
    FinalizePlanView,
)

urlpatterns = [
    # Исследования
    path("studies/", StudyListView.as_view(), name="study-list"),
    path("studies/<int:pk>/", StudyDetailView.as_view(), name="study-detail"),
    path("studies/<int:pk>/generate/",
         GenerateRecommendationsView.as_view(), name="study-generate"),
    path("studies/<int:pk>/add-recommendation/",
         AddDoctorRecommendationView.as_view(), name="study-add-rec"),
    path("studies/<int:pk>/finalize/",
         FinalizePlanView.as_view(), name="study-finalize"),

    # Рекомендации
    path("recommendations/<int:pk>/review/",
         ReviewRecommendationView.as_view(), name="recommendation-review"),
]
from django.urls import path
from .views import (
    StudyListView,
    StudyDetailView,
    GenerateRecommendationsView,
    EditRecommendationView,
    ApproveRecommendationView,
    RejectRecommendationView,
    AddDoctorRecommendationView,
)

urlpatterns = [
    # Исследования
    path("studies/", StudyListView.as_view(), name="study-list"),
    path("studies/<int:pk>/", StudyDetailView.as_view(), name="study-detail"),
    path("studies/<int:pk>/generate/",
         GenerateRecommendationsView.as_view(), name="study-generate"),
    path("studies/<int:pk>/add-recommendation/",
         AddDoctorRecommendationView.as_view(), name="study-add-rec"),

    path("recommendations/<int:pk>/edit/",
         EditRecommendationView.as_view(), name="recommendation-edit"),
    path("recommendations/<int:pk>/approve/",
         ApproveRecommendationView.as_view(), name="recommendation-approve"),
    path("recommendations/<int:pk>/reject/",
         RejectRecommendationView.as_view(), name="recommendation-reject"),
]
from django.urls import path
from .views import StudyListView, StudyDetailView, GenerateRecommendationsView


urlpatterns = [
    path('studies/', StudyListView.as_view(), name='study-list'),
    path('studies/<int:pk>/', StudyDetailView.as_view(), name='study-detail'),
    path('studies/<int:pk>/generate/', GenerateRecommendationsView.as_view(), name='study-generate'),
]
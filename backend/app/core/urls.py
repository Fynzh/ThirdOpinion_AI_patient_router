from django.urls import path
from .views import StudyListView, StudyDetailView


urlpatterns = [
    path('studies/', StudyListView.as_view(), name='study-list'),
    path('studies/<int:pk>/', StudyDetailView.as_view(), name='study-detail'),
]
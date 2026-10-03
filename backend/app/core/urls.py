from django.urls import path
from .views import StudyListView


urlpatterns = [
    path('studies/', StudyListView.as_view(), name='study-list'),
]
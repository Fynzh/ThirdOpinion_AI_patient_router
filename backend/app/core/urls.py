from django.urls import path

from .views import (
    StudyListCreateView,
    StudyDetailView,
    StudyUpdateView,
    StudyUploadFileView,
    StudyDownloadFileView,
    GenerateRecommendationsView,
    AddDoctorRecommendationView,
    UpdateCarePlanCommentView,
    SendCarePlanView,
    EditRecommendationView,
    ApproveRecommendationView,
    RejectRecommendationView,
    PatientListCreateView,
    PatientDetailView,
    PatientAvailableStudiesView,
)
from .auth_views import RegisterView, LoginView, LogoutView, MeView


urlpatterns = [
    # ---- Авторизация ----
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),

    # ---- Пациенты ----
    path("patients/", PatientListCreateView.as_view(), name="patient-list"),
    path("patients/<int:pk>/", PatientDetailView.as_view(), name="patient-detail"),
    path(
        "patients/<int:pk>/available-studies/",
        PatientAvailableStudiesView.as_view(),
        name="patient-available-studies",
    ),

    # ---- Исследования ----
    path("studies/", StudyListCreateView.as_view(), name="study-list-create"),
    path("studies/<int:pk>/", StudyDetailView.as_view(), name="study-detail"),
    path("studies/<int:pk>/update/", StudyUpdateView.as_view(), name="study-update"),
    path("studies/<int:pk>/upload-file/", StudyUploadFileView.as_view(), name="study-upload-file"),
    path("studies/<int:pk>/file/", StudyDownloadFileView.as_view(), name="study-file"),

    # ---- ИИ ----
    path("studies/<int:pk>/generate/", GenerateRecommendationsView.as_view(), name="study-generate"),
    path("studies/<int:pk>/add-recommendation/", AddDoctorRecommendationView.as_view(), name="study-add-rec"),

    # ---- Рекомендации ----
    path("recommendations/<int:pk>/edit/", EditRecommendationView.as_view(), name="recommendation-edit"),
    path("recommendations/<int:pk>/approve/", ApproveRecommendationView.as_view(), name="recommendation-approve"),
    path("recommendations/<int:pk>/reject/", RejectRecommendationView.as_view(), name="recommendation-reject"),

    # ---- План ----
    path("studies/<int:pk>/care-plan/", UpdateCarePlanCommentView.as_view(), name="study-care-plan"),
    path("studies/<int:pk>/send/", SendCarePlanView.as_view(), name="study-send"),
]
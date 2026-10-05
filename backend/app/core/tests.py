"""
Автотесты REST API.

Запуск (из backend/app):
    python manage.py test core -v 2

Внешних зависимостей не требуют: ИИ (GigaChat) подменён заглушкой, письма
уходят в память, реестр пациентов и MEDIA_ROOT — во временных папках.
"""
import json
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from core import patient_registry
from core.models import CarePlan, Patient, Recommendation, Study

FAKE_AI_RESULT = {
    "status": "findings",
    "summary": "",
    "recommendations": [
        {
            "specialist": "Пульмонолог",
            "specialty_code": "pulmonology",
            "reasoning": "Очаг в правом лёгком",
            "priority": "high",
            "confidence": 0.9,
        }
    ],
}

TMP_MEDIA = tempfile.mkdtemp(prefix="test_media_")
LOCMEM_MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}


def tearDownModule():
    shutil.rmtree(TMP_MEDIA, ignore_errors=True)


@override_settings(MEDIA_ROOT=TMP_MEDIA, MAILERS=LOCMEM_MAILERS)
class ApiTestCase(APITestCase):
    """Общая обвязка: токен, временный реестр, заглушка ИИ."""

    def setUp(self):
        # Реестр персональных данных — во временный файл
        self._registry_dir = tempfile.mkdtemp(prefix="test_registry_")
        patcher = mock.patch.object(
            patient_registry, "REGISTRY_PATH", Path(self._registry_dir) / "registry.json"
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self._registry_dir, True)

        # ИИ — заглушка (по умолчанию одна рекомендация от «ИИ»)
        ai = mock.patch(
            "nlp_module.analyzer.generate_recommendations",
            return_value=json.loads(json.dumps(FAKE_AI_RESULT)),
        )
        self.ai = ai.start()
        self.addCleanup(ai.stop)

        user = User.objects.create_user("doctor", password="secret123")
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # ---------- помощники ----------
    def make_patient(self, email="patient@example.com", **extra):
        payload = {
            "full_name": "Иванов Иван Иванович",
            "birth_date": "1990-05-17",
            "sex": "M",
            "age": 36,
            "phone": "+7 (903) 987-98-98",
            "email": email,
            **extra,
        }
        res = self.client.post("/api/patients/", payload, format="json")
        self.assertEqual(res.status_code, 201, res.content)
        return res.json()

    def make_study(self, patient_id, **extra):
        payload = {
            "patient": patient_id,
            "modality": "CHEST_CT",
            "study_date": "2026-01-15",
            "radiologist_conclusion": "Очаг в правом лёгком.",
            **extra,
        }
        res = self.client.post("/api/studies/", payload, format="multipart")
        self.assertEqual(res.status_code, 201, res.content)
        return res.json()

    def study_with_pending_rec(self, **patient_extra):
        patient = self.make_patient(**patient_extra)
        study = self.make_study(patient["id"])
        rec = Recommendation.objects.get(study_id=study["id"])
        return patient, study, rec

    def approve_all(self, study_id):
        for rec in Recommendation.objects.filter(study_id=study_id):
            res = self.client.post(f"/api/recommendations/{rec.id}/approve/")
            self.assertEqual(res.status_code, 200, res.content)


# ============================================================
# Авторизация
# ============================================================
class AuthTests(ApiTestCase):
    def test_requests_without_token_are_rejected(self):
        self.client.credentials()  # убираем токен
        self.assertEqual(self.client.get("/api/studies/").status_code, 401)
        self.assertEqual(self.client.get("/api/patients/").status_code, 401)

    def test_me_returns_current_user(self):
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["username"], "doctor")


# ============================================================
# Пациенты
# ============================================================
class PatientTests(ApiTestCase):
    def test_create_patient_writes_personal_data_to_registry(self):
        patient = self.make_patient()
        self.assertEqual(patient["full_name"], "Иванов Иван Иванович")
        self.assertEqual(patient["email"], "patient@example.com")
        self.assertTrue(patient["patient_code"].startswith("PAT-"))

        stored = patient_registry.get_personal_data(patient["patient_code"])
        self.assertEqual(stored["phone"], "+7 (903) 987-98-98")

    def test_create_patient_validation_error(self):
        res = self.client.post("/api/patients/", {"age": 30, "sex": "X"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "VALIDATION_ERROR")

    def test_list_and_detail(self):
        patient = self.make_patient()
        listing = self.client.get("/api/patients/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([p["id"] for p in listing.json()], [patient["id"]])

        detail = self.client.get(f"/api/patients/{patient['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(self.client.get("/api/patients/9999/").status_code, 404)

    def test_patch_updates_registry(self):
        patient = self.make_patient()
        res = self.client.patch(
            f"/api/patients/{patient['id']}/", {"phone": "+7 (900) 111-22-33"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["phone"], "+7 (900) 111-22-33")

    def test_available_studies(self):
        patient = self.make_patient()
        self.assertEqual(
            self.client.get(f"/api/patients/{patient['id']}/available-studies/").json(), []
        )

        study = self.make_study(patient["id"])
        res = self.client.get(f"/api/patients/{patient['id']}/available-studies/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([s["id"] for s in res.json()], [study["id"]])

        # фильтры has_plan
        no_plan = self.client.get(
            f"/api/patients/{patient['id']}/available-studies/?has_plan=false"
        )
        self.assertEqual(len(no_plan.json()), 1)
        with_plan = self.client.get(
            f"/api/patients/{patient['id']}/available-studies/?has_plan=true"
        )
        self.assertEqual(with_plan.json(), [])

    def test_available_studies_unknown_patient(self):
        self.assertEqual(self.client.get("/api/patients/9999/available-studies/").status_code, 404)


# ============================================================
# Исследования
# ============================================================
class StudyTests(ApiTestCase):
    def test_create_study_runs_ai_automatically(self):
        patient = self.make_patient()
        study = self.make_study(patient["id"])

        self.assertEqual(study["patient"]["id"], patient["id"])
        db_study = Study.objects.get(id=study["id"])
        self.assertEqual(db_study.status, "ai_done")
        recs = db_study.recommendations.all()
        self.assertEqual(recs.count(), 1)
        self.assertEqual(recs[0].source, "ai")
        self.assertEqual(recs[0].status, "pending")

    def test_create_study_requires_conclusion(self):
        patient = self.make_patient()
        res = self.client.post(
            "/api/studies/",
            {"patient": patient["id"], "modality": "MAMMO", "study_date": "2026-01-15"},
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "VALIDATION_ERROR")

    def test_list_contains_plan_flags(self):
        patient = self.make_patient()
        self.make_study(patient["id"])
        res = self.client.get("/api/studies/")
        self.assertEqual(res.status_code, 200, res.content)
        row = res.json()[0]
        self.assertEqual(row["patient_full_name"], "Иванов Иван Иванович")
        self.assertIs(row["has_draft_plan"], False)
        self.assertIs(row["has_sent_plan"], False)

    def test_detail_without_plan(self):
        patient = self.make_patient()
        study = self.make_study(patient["id"])
        res = self.client.get(f"/api/studies/{study['id']}/")
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIsNone(res.json()["care_plan"])
        self.assertEqual(len(res.json()["recommendations"]), 1)

    def test_detail_not_found(self):
        self.assertEqual(self.client.get("/api/studies/9999/").status_code, 404)

    def test_update_study(self):
        patient = self.make_patient()
        study = self.make_study(patient["id"])
        res = self.client.patch(
            f"/api/studies/{study['id']}/update/",
            {"title": "Очаг в лёгком", "slices_count": 120},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["title"], "Очаг в лёгком")

    def test_file_upload_and_download(self):
        patient = self.make_patient()
        study = self.make_study(patient["id"])

        # у исследования ещё нет файла
        self.assertEqual(self.client.get(f"/api/studies/{study['id']}/file/").status_code, 404)

        upload = SimpleUploadedFile("scan.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        res = self.client.post(
            f"/api/studies/{study['id']}/upload-file/", {"file": upload}, format="multipart"
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertTrue(res.json()["success"])

        download = self.client.get(f"/api/studies/{study['id']}/file/")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b"".join(download.streaming_content), b"%PDF-1.4 test")

    def test_upload_without_file(self):
        patient = self.make_patient()
        study = self.make_study(patient["id"])
        res = self.client.post(f"/api/studies/{study['id']}/upload-file/", {}, format="multipart")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "FILE_REQUIRED")

    def test_generate_replaces_ai_recommendations(self):
        _, study, old_rec = self.study_with_pending_rec()
        res = self.client.post(f"/api/studies/{study['id']}/generate/")
        self.assertEqual(res.status_code, 200, res.content)
        self.assertFalse(Recommendation.objects.filter(id=old_rec.id).exists())
        self.assertEqual(Recommendation.objects.filter(study_id=study["id"]).count(), 1)

    def test_generate_nlp_parse_error(self):
        from nlp_module.analyzer import RecommendationError

        _, study, _ = self.study_with_pending_rec()
        self.ai.side_effect = RecommendationError("мусор")
        res = self.client.post(f"/api/studies/{study['id']}/generate/")
        self.assertEqual(res.status_code, 502)
        self.assertEqual(res.json()["code"], "NLP_PARSE_ERROR")

    def test_generate_unknown_study(self):
        self.assertEqual(self.client.post("/api/studies/9999/generate/").status_code, 404)


# ============================================================
# Рекомендации
# ============================================================
class RecommendationTests(ApiTestCase):
    def test_approve_and_reject(self):
        _, _, rec = self.study_with_pending_rec()

        res = self.client.post(f"/api/recommendations/{rec.id}/approve/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "approved")

        res = self.client.post(f"/api/recommendations/{rec.id}/reject/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "rejected")

    def test_edit_resets_to_pending_and_marks_doctor(self):
        _, _, rec = self.study_with_pending_rec()
        self.client.post(f"/api/recommendations/{rec.id}/approve/")

        res = self.client.patch(
            f"/api/recommendations/{rec.id}/edit/",
            {"reasoning": "Уточнённое обоснование", "priority": "low"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.content)
        data = res.json()
        self.assertEqual(data["reasoning"], "Уточнённое обоснование")
        self.assertEqual(data["priority"], "low")
        self.assertEqual(data["source"], "doctor")
        self.assertEqual(data["status"], "pending")

    def test_unknown_recommendation(self):
        self.assertEqual(self.client.post("/api/recommendations/9999/approve/").status_code, 404)
        self.assertEqual(self.client.post("/api/recommendations/9999/reject/").status_code, 404)
        self.assertEqual(
            self.client.patch("/api/recommendations/9999/edit/", {}, format="json").status_code, 404
        )

    def test_add_doctor_recommendation(self):
        _, study, _ = self.study_with_pending_rec()
        res = self.client.post(
            f"/api/studies/{study['id']}/add-recommendation/",
            {"specialist": "Онколог", "reasoning": "Исключить онкопатологию", "priority": "high"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()["source"], "doctor")
        self.assertEqual(res.json()["status"], "approved")

    def test_add_doctor_recommendation_validation(self):
        _, study, _ = self.study_with_pending_rec()
        res = self.client.post(
            f"/api/studies/{study['id']}/add-recommendation/",
            {"specialist": "", "reasoning": ""},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "VALIDATION_ERROR")


# ============================================================
# План обращения: комментарий и отправка
# ============================================================
class CarePlanTests(ApiTestCase):
    def test_plan_is_created_when_all_recommendations_checked(self):
        _, study, _ = self.study_with_pending_rec()
        self.assertFalse(CarePlan.objects.filter(study_id=study["id"]).exists())

        self.approve_all(study["id"])

        plan = CarePlan.objects.get(study_id=study["id"])
        self.assertEqual(plan.status, "draft")
        self.assertEqual(plan.recommendations_snapshot[0]["specialist"], "Пульмонолог")
        self.assertEqual(Study.objects.get(id=study["id"]).status, "in_review")

        detail = self.client.get(f"/api/studies/{study['id']}/")
        self.assertEqual(detail.status_code, 200, detail.content)
        self.assertEqual(detail.json()["care_plan"]["status"], "draft")

        row = self.client.get("/api/studies/").json()[0]
        self.assertIs(row["has_draft_plan"], True)

    def test_comment_before_plan_exists(self):
        _, study, _ = self.study_with_pending_rec()
        res = self.client.patch(
            f"/api/studies/{study['id']}/care-plan/", {"doctor_comment": "x"}, format="json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "NO_DRAFT_PLAN")

    def test_update_comment(self):
        _, study, _ = self.study_with_pending_rec()
        self.approve_all(study["id"])

        res = self.client.patch(
            f"/api/studies/{study['id']}/care-plan/",
            {"doctor_comment": "Явиться в течение недели"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["doctor_comment"], "Явиться в течение недели")

    def test_update_comment_requires_field(self):
        _, study, _ = self.study_with_pending_rec()
        self.approve_all(study["id"])
        res = self.client.patch(f"/api/studies/{study['id']}/care-plan/", {}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "VALIDATION_ERROR")

    def test_comment_survives_plan_rebuild(self):
        _, study, rec = self.study_with_pending_rec()
        self.approve_all(study["id"])
        self.client.patch(
            f"/api/studies/{study['id']}/care-plan/", {"doctor_comment": "Важно"}, format="json"
        )

        # врач правит рекомендацию и снова одобряет -> снимок пересобирается
        self.client.patch(
            f"/api/recommendations/{rec.id}/edit/", {"priority": "low"}, format="json"
        )
        self.client.post(f"/api/recommendations/{rec.id}/approve/")

        plan = CarePlan.objects.get(study_id=study["id"])
        self.assertEqual(plan.doctor_comment, "Важно")
        self.assertEqual(plan.recommendations_snapshot[0]["priority"], "low")

    def test_send_plan(self):
        _, study, _ = self.study_with_pending_rec()
        self.approve_all(study["id"])
        self.client.patch(
            f"/api/studies/{study['id']}/care-plan/", {"doctor_comment": "Спасибо"}, format="json"
        )

        res = self.client.post(f"/api/studies/{study['id']}/send/")
        self.assertEqual(res.status_code, 200, res.content)
        self.assertTrue(res.json()["success"])
        self.assertEqual(res.json()["plan"]["status"], "sent")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["patient@example.com"])

        plan = CarePlan.objects.get(study_id=study["id"])
        self.assertEqual(plan.status, "sent")
        self.assertIsNotNone(plan.sent_at)
        self.assertEqual(Study.objects.get(id=study["id"]).status, "sent")

    def test_plan_cannot_be_sent_or_edited_twice(self):
        _, study, _ = self.study_with_pending_rec()
        self.approve_all(study["id"])
        self.client.post(f"/api/studies/{study['id']}/send/")

        again = self.client.post(f"/api/studies/{study['id']}/send/")
        self.assertEqual(again.status_code, 400)
        self.assertEqual(again.json()["code"], "PLAN_ALREADY_SENT")

        edit = self.client.patch(
            f"/api/studies/{study['id']}/care-plan/", {"doctor_comment": "позже"}, format="json"
        )
        self.assertEqual(edit.status_code, 400)
        self.assertEqual(edit.json()["code"], "PLAN_ALREADY_SENT")
        self.assertEqual(len(mail.outbox), 1)

        row = self.client.get("/api/studies/").json()[0]
        self.assertIs(row["has_sent_plan"], True)

    def test_send_without_plan(self):
        _, study, _ = self.study_with_pending_rec()
        res = self.client.post(f"/api/studies/{study['id']}/send/")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "NO_DRAFT_PLAN")

    def test_send_without_patient_email(self):
        _, study, _ = self.study_with_pending_rec(email="")
        self.approve_all(study["id"])
        res = self.client.post(f"/api/studies/{study['id']}/send/")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "NO_PATIENT_EMAIL")
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(CarePlan.objects.get(study_id=study["id"]).status, "draft")

    def test_send_unknown_study(self):
        self.assertEqual(self.client.post("/api/studies/9999/send/").status_code, 404)
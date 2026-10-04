import type { StudyDetail, StudyListItem, NewStudyPayload } from '@/types/study';
import type {
  AddDoctorRecommendationPayload,
  GenerateRecommendationsResponse,
  Recommendation,
} from '@/types/recommendation';
import type { CarePlan, SendCarePlanResponse } from '@/types/care-plan';
import { ApiError, getJson, patchJson, postForm, postJson, unwrapList } from './http';
import { getToken } from './token';

export async function fetchStudies(): Promise<StudyListItem[]> {
  return unwrapList(await getJson<StudyListItem[]>('/api/studies/'));
}

export const fetchStudy = (id: number) =>
  getJson<StudyDetail>(`/api/studies/${id}/`);

/** Повторный запуск ИИ (для нового исследования он стартует сам) */
export const generateRecommendations = (studyId: number) =>
  postJson<GenerateRecommendationsResponse>(`/api/studies/${studyId}/generate/`);

export const addDoctorRecommendation = (studyId: number, payload: AddDoctorRecommendationPayload) =>
  postJson<Recommendation>(`/api/studies/${studyId}/add-recommendation/`, payload);

export function createStudy(payload: NewStudyPayload) {
  const form = new FormData();
  form.append('patient', String(payload.patient));
  form.append('modality', payload.modality);
  form.append('study_date', payload.study_date);
  form.append('radiologist_conclusion', payload.radiologist_conclusion);
  if (payload.file) form.append('file', payload.file);
  return postForm<StudyDetail>('/api/studies/', form);
}

/** Комментарий врача (только пока план в статусе draft) */
export const updateCarePlanComment = (studyId: number, doctorComment: string) =>
  patchJson<CarePlan>(`/api/studies/${studyId}/care-plan/`, { doctor_comment: doctorComment });

/** Отправка плана пациенту на email */
export const sendCarePlan = (studyId: number) =>
  postJson<SendCarePlanResponse>(`/api/studies/${studyId}/send/`);

/** Файл отдаётся только с токеном, поэтому обычная ссылка не подходит: качаем через fetch */
export async function downloadStudyFile(studyId: number, fileName: string) {
  const token = getToken();
  const res = await fetch(`/api/studies/${studyId}/file/`, {
    headers: token ? { Authorization: `Token ${token}` } : {},
  });

  if (!res.ok) {
    let message = `Не удалось скачать файл (${res.status})`;
    try {
      message = (await res.json()).error ?? message;
    } catch {
      /* тело не JSON */
    }
    throw new ApiError(message, res.status);
  }

  const url = URL.createObjectURL(await res.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
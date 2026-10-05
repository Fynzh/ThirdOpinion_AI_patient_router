import type { ISODate, ISODateTime } from "./common";
import type { Patient } from "./patient";
import type { Recommendation } from "./recommendation";
import type { CarePlan } from "./care-plan";

export const MODALITY_LABELS = {
  CHEST_XRAY: "Рентгенограмма грудной клетки",
  FLG: "ФЛГ",
  CHEST_CT: "КТ органов грудной клетки",
  BRAIN_CT: "КТ головного мозга",
  MAMMO: "Маммограмма",
} as const;

export const STUDY_STATUS_LABELS = {
  processing: "Новое — ждёт обработки ИИ",
  ai_done: "ИИ обработал — ждёт врача",
  in_review: "Врач проверяет",
  approved: "План утверждён",
  sent: "Отправлено пациенту",
} as const;

export type Modality = keyof typeof MODALITY_LABELS;
export type StudyStatus = keyof typeof STUDY_STATUS_LABELS;

/** StudyListSerializer: строка таблицы */
export interface StudyListItem {
  id: number;
  patient: number;
  patient_code: string;
  patient_full_name: string;
  display_title: string; // title или первая строка заключения
  title: string;
  modality: Modality;
  modality_display: string;
  study_date: ISODate;
  slices_count: number | null;
  status: StudyStatus;
  status_display: string;
  recommendations_count: number;
  has_draft_plan: boolean;
  has_sent_plan: boolean;
  created_at: ISODateTime;
}

/** StudyDetailSerializer: карточка исследования */
export interface StudyDetail {
  id: number;
  patient: Patient;
  title: string;
  modality: Modality;
  modality_display: string;
  study_date: ISODate;
  slices_count: number | null;
  radiologist_conclusion: string;
  file: string | null;
  status: StudyStatus;
  status_display: string;
  recommendations: Recommendation[];
  care_plan: CarePlan | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

/** Данные для POST /api/studies/ (отправляется как multipart) */
export interface NewStudyPayload {
  patient: number;
  modality: Modality;
  study_date: ISODate;
  radiologist_conclusion: string;
  file: File | null;
}
import type { ISODateTime } from "./common";

export const CARE_PLAN_STATUS_LABELS = {
  draft: "Черновик",
  approved: "Утверждён",
  sent: "Отправлен пациенту",
} as const;

export type CarePlanStatus = keyof typeof CARE_PLAN_STATUS_LABELS;

export interface CarePlan {
  id: number;
  study: number;
  approved_by: number | null;
  recommendations_snapshot: unknown[]; // заполняет сервер
  doctor_comment: string;
  status: CarePlanStatus;
  status_display: string;
  created_at: ISODateTime;
  approved_at: ISODateTime | null;
  sent_at: ISODateTime | null;
}

export interface FinalizePlanPayload {
  doctor_comment?: string;
}
import type { ISODateTime } from './common';
import type { Priority } from './recommendation';

export const CARE_PLAN_STATUS_LABELS = {
  draft: 'Черновик',
  sent: 'Отправлено',
} as const;

export type CarePlanStatus = keyof typeof CARE_PLAN_STATUS_LABELS;

export interface CarePlanItem {
  specialist: string;
  reasoning: string;
  priority: Priority;
}

export interface CarePlan {
  id: number;
  study: number;
  recommendations_snapshot: CarePlanItem[];
  doctor_comment: string;
  status: CarePlanStatus;
  status_display: string;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  sent_at: ISODateTime | null;
}

export interface SendCarePlanResponse {
  success: boolean;
  message: string;
  plan: CarePlan;
}
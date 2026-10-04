import type { ISODateTime } from './common';

export const RECOMMENDATION_SOURCE_LABELS = { ai: 'ИИ', doctor: 'Врач' } as const;

export const RECOMMENDATION_STATUS_LABELS = {
  pending: 'Ожидает проверки',
  approved: 'Одобрена',
  edited: 'Изменена врачом',
  rejected: 'Отклонена',
} as const;

export const PRIORITY_LABELS = { high: 'Высокий', medium: 'Средний', low: 'Низкий' } as const;

export type RecommendationSource = keyof typeof RECOMMENDATION_SOURCE_LABELS;
export type RecommendationStatus = keyof typeof RECOMMENDATION_STATUS_LABELS;
export type Priority = keyof typeof PRIORITY_LABELS;

export interface Recommendation {
  id: number;
  study: number;
  source: RecommendationSource;
  source_display: string;
  status: RecommendationStatus;
  status_display: string;
  specialist: string;
  specialty_code: string;
  reasoning: string;
  priority: Priority;
  priority_display: string;
  confidence: number | null;
  study_conclusion: string;
  doctor_comment: string;
  raw_model_output: Record<string, unknown>;
  reviewed_by: number | null;
  reviewed_at: ISODateTime | null;
  created_at: ISODateTime;
}

/** Что врач может менять при проверке (PATCH) */
export type RecommendationReviewPayload = Partial<
  Pick<Recommendation, 'status' | 'specialist' | 'reasoning' | 'priority' | 'doctor_comment'>
>;
export type ISODate = string;     // 'YYYY-MM-DD'
export type ISODateTime = string; // '2026-10-04T12:30:00Z'

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type ApiErrorCode =
  | 'STUDY_NOT_FOUND'
  | 'RECOMMENDATION_NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'NLP_PARSE_ERROR'
  | 'NLP_ERROR'
  | 'INVALID_CREDENTIALS'
  | 'WEAK_PASSWORD'
  | 'USER_EXISTS'
  | 'PLAN_ALREADY_SENT'
  | 'NO_DRAFT_PLAN'
  | 'NO_PATIENT_EMAIL'
  | 'EMAIL_SEND_ERROR'
  | 'PATIENT_NOT_FOUND';

export interface ApiErrorBody {
  error: string;
  code?: ApiErrorCode;
}


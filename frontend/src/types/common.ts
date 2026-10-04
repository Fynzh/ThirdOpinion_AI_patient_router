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
  | 'NO_APPROVED_RECOMMENDATIONS';

export interface ApiErrorBody {
  error: string;
  code?: ApiErrorCode;
}
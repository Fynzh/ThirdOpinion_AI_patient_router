export type ISODate = string;     // 'YYYY-MM-DD'
export type ISODateTime = string; // '2026-10-04T12:30:00Z'

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
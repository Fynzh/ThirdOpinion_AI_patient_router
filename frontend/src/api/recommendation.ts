import type { EditRecommendationPayload, Recommendation } from '@/types/recommendation';
import { patchJson, postJson } from './http';

export const editRecommendation = (id: number, payload: EditRecommendationPayload) =>
  patchJson<Recommendation>(`/api/recommendations/${id}/edit/`, payload);

export const approveRecommendation = (id: number) =>
  postJson<Recommendation>(`/api/recommendations/${id}/approve/`);

export const rejectRecommendation = (id: number) =>
  postJson<Recommendation>(`/api/recommendations/${id}/reject/`);
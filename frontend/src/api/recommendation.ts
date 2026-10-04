import type {
  EditRecommendationPayload,
  Recommendation,
  RecommendationDecisionPayload,
} from '@/types/recommendation';
import { patchJson, postJson } from './http';

export const editRecommendation = (id: number, payload: EditRecommendationPayload) =>
  patchJson<Recommendation>(`/api/recommendations/${id}/edit/`, payload);

export const approveRecommendation = (id: number, payload: RecommendationDecisionPayload = {}) =>
  postJson<Recommendation>(`/api/recommendations/${id}/approve/`, payload);

export const rejectRecommendation = (id: number, payload: RecommendationDecisionPayload = {}) =>
  postJson<Recommendation>(`/api/recommendations/${id}/reject/`, payload);
import type { StudyListItem } from '@/types/study';
import { USE_MOCK, delay, getJson, unwrapList } from './http';

const MOCK_STUDIES: StudyListItem[] = [
  {
    id: 1, patient: 1, patient_code: 'PAT-2026-0001',
    modality: 'MAMMO', modality_display: 'Маммограмма',
    study_date: '2022-09-27', status: 'ai_done', status_display: 'ИИ обработал — ждёт врача',
    recommendations_count: 3, created_at: '2026-05-21T15:09:00Z',
  },
  {
    id: 2, patient: 2, patient_code: 'PAT-2026-0002',
    modality: 'MAMMO', modality_display: 'Маммограмма',
    study_date: '2014-02-17', status: 'approved', status_display: 'План утверждён',
    recommendations_count: 2, created_at: '2026-05-21T14:55:00Z',
  },
  {
    id: 3, patient: 3, patient_code: null,
    modality: 'MAMMO', modality_display: 'Маммограмма',
    study_date: '2023-08-02', status: 'new', status_display: 'Новое — ждёт обработки ИИ',
    recommendations_count: 0, created_at: '2026-05-21T14:40:00Z',
  },
];

export async function fetchStudies(): Promise<StudyListItem[]> {
  if (USE_MOCK) {
    await delay(400);
    return MOCK_STUDIES;
  }
  return unwrapList(await getJson<StudyListItem[]>('/api/studies/'));
}
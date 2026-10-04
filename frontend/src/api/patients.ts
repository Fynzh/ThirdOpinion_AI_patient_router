import type { PatientSummary } from '@/types/patient';
import { USE_MOCK, delay } from './http';
import { fetchStudies } from './studies';

const MOCK_PATIENTS: PatientSummary[] = [
  { id: 1, patient_code: 'PAT-2026-A3F8B1', full_name: 'Тестовый Пациент Первый' },
  { id: 2, patient_code: 'PAT-2026-B7C2D9', full_name: 'Тестовый Пациент Второй' },
  { id: 3, patient_code: 'PAT-2026-C1E4F0', full_name: '' }, // нет в реестре
];

export async function fetchPatients(): Promise<PatientSummary[]> {
  if (USE_MOCK) {
    await delay(400);
    return MOCK_PATIENTS;
  }

  // Временно: пациенты из списка исследований, без дублей
  const studies = await fetchStudies();
  const unique = new Map<number, PatientSummary>();
  for (const st of studies) {
    unique.set(st.patient, {
      id: st.patient,
      patient_code: st.patient_code,
      full_name: st.patient_full_name,
    });
  }
  return [...unique.values()];
}
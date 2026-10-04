import type { NewPatientPayload, Patient, PatientSummary } from '@/types/patient';
import { USE_MOCK, delay } from './http';
import { fetchStudies } from './studies';
import type { AvailableStudy } from '@/types/study';
import { postJson } from './http';

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
  return [...unique.values()].sort((a, b) =>
  (a.full_name || a.patient_code).localeCompare(b.full_name || b.patient_code, 'ru'),
);
}

export const createPatient = (payload: NewPatientPayload) =>
  postJson<Patient>('/api/patients/', payload);

/** TODO: GET /api/patients/<id>/available-studies/, бэк пока не реализовал */
export async function fetchAvailableStudies(patientId: number): Promise<AvailableStudy[]> {
  void patientId;
  return [];
}
import type { PatientAnonymized } from '@/types/patient';
import { USE_MOCK, delay, getJson, unwrapList } from './http';

const MOCK_PATIENTS: PatientAnonymized[] = [
  { id: 1, patient_code: 'PAT-2026-0001' },
  { id: 2, patient_code: 'PAT-2026-0002' },
  { id: 3, patient_code: null },
];

export async function fetchPatients(): Promise<PatientAnonymized[]> {
  if (USE_MOCK) {
    await delay(400);
    return MOCK_PATIENTS;
  }
  // Адрес примерный, уточните у бэкендера
  return unwrapList(await getJson<PatientAnonymized[]>('/api/patients/'));
}
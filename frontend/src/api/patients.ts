import type { NewPatientPayload, Patient, PatientSummary } from '@/types/patient';
import type { StudyListItem } from '@/types/study';
import { getJson, postJson, unwrapList } from './http';

export async function fetchPatients(): Promise<PatientSummary[]> {
  const patients = unwrapList(await getJson<Patient[]>('/api/patients/'));
  return patients
    .map(({ id, patient_code, full_name }) => ({ id, patient_code, full_name }))
    .sort((a, b) =>
      (a.full_name || a.patient_code).localeCompare(b.full_name || b.patient_code, 'ru'),
    );
}

export const createPatient = (payload: NewPatientPayload) =>
  postJson<Patient>('/api/patients/', payload);

export const fetchAvailableStudies = (patientId: number) =>
  getJson<StudyListItem[]>(`/api/patients/${patientId}/available-studies/`);
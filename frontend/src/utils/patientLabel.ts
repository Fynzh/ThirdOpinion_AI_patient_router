import type { PatientSummary } from '@/types/patient';

export const getPatientLabel = (p: PatientSummary) => p.full_name || p.patient_code;
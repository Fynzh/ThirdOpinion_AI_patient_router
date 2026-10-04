import type { Patient } from '@/types/patient';

const USE_MOCK = true;

const MOCK_PATIENTS: Patient[] = [
  { id: '1', fullName: 'Пациент Тестовый 1' },
  { id: '2', fullName: 'Пациент Тестовый 2' },
  { id: '3', fullName: 'Пациент Тестовый 3' },
]

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export async function fetchPatients(): Promise<Patient[]> {
  if (USE_MOCK) {
    await delay(400); // имитация сетевого запроса, чтобы видеть состояние загрузки
    return MOCK_PATIENTS;
  }

  const response = await fetch('/api/patients/');
  if (!response.ok) {
    throw new Error(`Не удалось загрузить пациентов (${response.status})`);

  }

  const data: Array<{ id: number; full_name: string }> = await response.json();
  return data.map((p)  => ({ id: String(p.id), fullName: p.full_name}));
}
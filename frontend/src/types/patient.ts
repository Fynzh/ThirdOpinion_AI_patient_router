import type { ISODate } from './common';

export type Sex = 'M' | 'F';

export const SEX_LABELS: Record<Sex, string> = { M: 'Мужской', F: 'Женский' };

/** PatientSerializer (вложен в карточку исследования) */
export interface Patient {
  id: number;
  patient_code: string;
  age: number;
  sex: Sex;
  full_name: string;  // '' если пациента нет в реестре
  birth_date: ISODate | ''; // '' если нет в реестре; формат берётся из JSON-реестра
  phone: string;
  email: string;
}

/** Минимум, который есть в списке исследований: из него собирается выпадающий список */
export type PatientSummary = Pick<Patient, 'id' | 'patient_code' | 'full_name'>;

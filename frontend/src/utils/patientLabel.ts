export const getPatientLabel = (id: number, code: string | null) =>
  code ?? `Пациент №${id}`;
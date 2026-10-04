/** Приводит любой ввод к виду +7 (903) 987-98-98 (форматирует по мере набора) */
export function formatPhone(raw: string): string {
  if (raw === '') return '';

  let d = raw.replace(/\D/g, '');
  if (d.startsWith('7') || d.startsWith('8')) d = d.slice(1); // префикс +7 или 8 при вставке
  d = d.slice(0, 10);

  let out = '+7 (' + d.slice(0, 3);
  if (d.length > 3) out += ') ' + d.slice(3, 6);
  if (d.length > 6) out += '-' + d.slice(6, 8);
  if (d.length > 8) out += '-' + d.slice(8, 10);
  return out;
}

export const isPhoneComplete = (value: string) => value.replace(/\D/g, '').length === 11;
/** Сегодня в локальной таймзоне, YYYY-MM-DD */
export const TODAY = new Date().toLocaleDateString('sv-SE');

/** Возраст по дате рождения YYYY-MM-DD; null, если дата некорректна или в будущем */
export function calcAge(birthIso: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(birthIso);
  if (!m) return null;
  const [y, mo, d] = m.slice(1).map(Number);
  const now = new Date();
  let age = now.getFullYear() - y;
  const hadBirthday =
    now.getMonth() + 1 > mo || (now.getMonth() + 1 === mo && now.getDate() >= d);
  if (!hadBirthday) age -= 1;
  return age >= 0 ? age : null;
}
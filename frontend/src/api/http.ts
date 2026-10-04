import type { Paginated } from '@/types/common';

export const USE_MOCK = true; // false, когда бэкенд готов

export const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { credentials: 'include' });
  if (!response.ok) throw new Error(`Ошибка запроса ${url}: ${response.status}`);
  return response.json() as Promise<T>;
}

/** Работает и с пагинацией DRF, и с обычным массивом */
export const unwrapList = <T>(data: T[] | Paginated<T>): T[] =>
  Array.isArray(data) ? data : data.results;
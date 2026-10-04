import type { ApiErrorBody, ApiErrorCode, Paginated } from '@/types/common';
import { clearToken, getToken } from './token';

export const USE_MOCK = false; // false, когда бэкенд готов

export const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class ApiError extends Error {
  status: number;
  code?: ApiErrorCode;

  constructor(message: string, status: number, code?: ApiErrorCode) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const PUBLIC_URLS = ['/api/auth/login/', '/api/auth/register/'];

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const isPublic = PUBLIC_URLS.includes(url);
  const token = isPublic ? null : getToken();

  const headers: Record<string, string> = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Token ${token}`;

  const response = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && !isPublic) {
    clearToken();
    window.location.assign('/login');
  }

  if (!response.ok) {
    let data: Partial<ApiErrorBody> = {};
    try { data = await response.json(); } catch { /* тело не JSON */ }
    throw new ApiError(data.error ?? `Ошибка запроса (${response.status})`, response.status, data.code);
  }
  return response.json() as Promise<T>;
}

export const getJson = <T>(url: string) => request<T>('GET', url);
export const postJson = <T>(url: string, body?: unknown) => request<T>('POST', url, body);
export const patchJson = <T>(url: string, body?: unknown) => request<T>('PATCH', url, body);

/** Работает и с пагинацией DRF, и с обычным массивом */
export const unwrapList = <T>(data: T[] | Paginated<T>): T[] =>
  Array.isArray(data) ? data : data.results;
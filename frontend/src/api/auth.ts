import type { AuthResponse, CurrentUser, LoginPayload, RegisterPayload } from '@/types/auth';
import { getJson, postJson } from './http';
import { clearToken, setToken } from './token';

export async function login(payload: LoginPayload) {
  const res = await postJson<AuthResponse>('/api/auth/login/', payload);
  setToken(res.token);
  return res.user;
}

export async function register(payload: RegisterPayload) {
  const res = await postJson<AuthResponse>('/api/auth/register/', payload);
  setToken(res.token);
  return res.user;
}

export async function logout() {
  try {
    await postJson('/api/auth/logout/');
  } catch {
    /* токен мог уже протухнуть, в любом случае выходим локально */
  } finally {
    clearToken();
  }
}

export const fetchMe = () => getJson<CurrentUser>('/api/auth/me/');
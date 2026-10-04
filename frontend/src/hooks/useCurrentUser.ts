import { fetchMe } from '@/api/auth';
import type { CurrentUser } from '@/types/auth';
import { useFetch } from './useFetch';

export function useCurrentUser() {
  const { data, isLoading, error } = useFetch<CurrentUser | null>(fetchMe, null);
  return { user: data, isLoading, error };
}
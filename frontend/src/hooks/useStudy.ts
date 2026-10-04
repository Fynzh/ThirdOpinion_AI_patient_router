import { useCallback } from 'react';
import { fetchStudy } from '@/api/studies';
import type { StudyDetail } from '@/types/study';
import { useFetch } from './useFetch';

export function useStudy(id: number) {
  const fetcher = useCallback(() => fetchStudy(id), [id]);
  const { data, isLoading, error, reload } = useFetch<StudyDetail | null>(fetcher, null);
  return { study: data, isLoading, error, reload };
}
import { useCallback } from 'react';
import { fetchAvailableStudies } from '@/api/patients';
import type { AvailableStudy } from '@/types/study';
import { useFetch } from './useFetch';

export function useAvailableStudies(patientId: number | null) {
  const fetcher = useCallback(
    () =>
      patientId === null
        ? Promise.resolve<AvailableStudy[]>([])
        : fetchAvailableStudies(patientId),
    [patientId],
  );
  const { data, isLoading } = useFetch<AvailableStudy[]>(fetcher, []);
  return { items: data, isLoading };
}
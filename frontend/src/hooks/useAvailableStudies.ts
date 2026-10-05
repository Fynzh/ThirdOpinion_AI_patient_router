import { useCallback } from 'react';
import { fetchAvailableStudies } from '@/api/patients';
import type { StudyListItem } from '@/types/study';
import { useFetch } from './useFetch';

export function useAvailableStudies(patientId: number | null) {
  const fetcher = useCallback(
    () =>
      patientId === null
        ? Promise.resolve<StudyListItem[]>([])
        : fetchAvailableStudies(patientId),
    [patientId],
  );
  const { data, isLoading } = useFetch<StudyListItem[]>(fetcher, []);
  return { items: data, isLoading };
}
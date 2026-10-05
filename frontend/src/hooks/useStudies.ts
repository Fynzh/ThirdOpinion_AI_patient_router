import { fetchStudies } from '@/api/studies';
import { useFetch } from './useFetch';

export function useStudies() {
  const { data, isLoading, error } = useFetch(fetchStudies, []);
  return { studies: data, isLoading, error };
}
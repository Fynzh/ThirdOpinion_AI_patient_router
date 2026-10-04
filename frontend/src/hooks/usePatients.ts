import { fetchPatients } from '@/api/patients';
import { useFetch } from './useFetch';

export function usePatients() {
  const { data, isLoading, error } = useFetch(fetchPatients, []);
  return { patients: data, isLoading, error };
}
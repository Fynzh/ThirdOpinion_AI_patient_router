import { useEffect, useState } from 'react';
import { fetchPatients } from '@/api/patients';
import type { Patient } from '@/types/patient';

export function usePatients() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false; // защита от обновления состояния после ухода со страницы

    fetchPatients()
      .then((data) => { if (!cancelled) setPatients(data); })
      .catch((e: Error) => { if (!cancelled) setError(e); })
      .finally(() => { if (!cancelled) setIsLoading(false); });

    return () => { cancelled = true; };
  }, []);

  return { patients, isLoading, error };
}
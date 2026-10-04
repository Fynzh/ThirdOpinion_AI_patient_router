import { useEffect, useState } from 'react';

export function useFetch<T>(fetcher: () => Promise<T>, initialData: T) {
  const [data, setData] = useState<T>(initialData);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetcher()
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e: Error) => { if (!cancelled) setError(e); })
      .finally(() => { if (!cancelled) setIsLoading(false); });
    return () => { cancelled = true; };
  }, [fetcher]);

  return { data, isLoading, error };
}
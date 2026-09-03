import { useState, useEffect } from 'react';
import { InspectionCase } from '../types';
import { fetchCases } from '../lib/api';

export function useCases() {
  const [cases, setCases] = useState<InspectionCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchCases()
      .then((data) => {
        if (isMounted) {
          setCases(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return { cases, loading, error };
}

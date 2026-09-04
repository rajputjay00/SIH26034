import { useState, useEffect } from 'react';
import { UserProfile } from '../types';

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('user_id');
      const role = localStorage.getItem('role');
      if (token && userId) {
        setUser({
          user_id: userId,
          username: userId,
          role: (role as any) || 'OFFICER',
          full_name: 'Inspector ' + userId,
          badge_number: 'LM-DEL-' + Math.floor(Math.random() * 10000)
        });
      }
      setLoading(false);
    }
  }, []);

  return {
    user,
    loading,
    isAuthenticated: !!user,
  };
}

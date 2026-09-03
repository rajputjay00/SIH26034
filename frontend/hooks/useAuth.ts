import { useState, useEffect } from 'react';
import { UserProfile } from '../types';

export function useAuth() {
  const [user, setUser] = useState<UserProfile>({
    user_id: "OFFICER-IND-1001",
    username: "officer1",
    role: "OFFICER",
    full_name: "Inspector R. K. Sharma",
    badge_number: "LM-DEL-4092"
  });
  const [loading, setLoading] = useState(false);

  return {
    user,
    loading,
    isAuthenticated: true,
  };
}

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';
import { Lock, User, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace('/inspections');
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!username || !password) {
      setError('Please enter both username and password.');
      return;
    }

    setLoading(true);
    try {
      await login(username, password);
      router.push('/inspections');
    } catch (err: any) {
      setError(err.message || 'Invalid credentials. Please try again.');
      setLoading(false);
    }
  };

  if (authLoading || isAuthenticated) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <RefreshCw className="w-8 h-8 animate-spin text-nirikshan-blue" />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-12 sm:px-6 lg:px-8 bg-slate-50 min-h-[80vh]">
      <div className="w-full max-w-md space-y-8 bg-white p-8 rounded-brand shadow-elevated border border-slate-200">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-nirikshan-navy rounded-full flex items-center justify-center mb-4">
            <ShieldCheck className="w-6 h-6 text-nirikshan-saffron" />
          </div>
          <h2 className="text-2xl font-bold text-nirikshan-navy tracking-tight">
            Officer Authentication
          </h2>
          <p className="mt-2 text-sm text-slate-500 font-medium">
            Authorized Legal Metrology Personnel Only
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-brand text-sm flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4 rounded-md shadow-xs">
            <div>
              <label className="block text-xs font-semibold text-nirikshan-navy mb-1.5" htmlFor="username">
                Officer ID / Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-brand text-sm placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-nirikshan-blue focus:border-nirikshan-blue transition-colors"
                  placeholder="Enter your Officer ID"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-nirikshan-navy mb-1.5" htmlFor="password">
                Secure Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-brand text-sm placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-nirikshan-blue focus:border-nirikshan-blue transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-bold rounded-brand text-white bg-nirikshan-navy hover:bg-nirikshan-navyDark focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-nirikshan-navy transition-all shadow-xs disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <span className="flex items-center space-x-2">
                  <Lock className="w-4 h-4 text-nirikshan-saffron" />
                  <span>Secure Login</span>
                </span>
              )}
            </button>
          </div>
        </form>
        
        <div className="pt-4 border-t border-slate-100 text-center text-xs text-slate-500">
          This system is restricted to authorized officers. All access is logged and monitored for security compliance.
        </div>
      </div>
    </div>
  );
}

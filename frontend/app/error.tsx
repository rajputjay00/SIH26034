'use client';

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="bg-white border border-gov-warning/30 rounded-gov p-6 max-w-md w-full shadow-xs text-center space-y-4">
        <div className="w-10 h-10 bg-gov-warningLight text-gov-warning rounded-full flex items-center justify-center mx-auto">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gov-navy">Application Error</h3>
          <p className="text-xs text-gov-muted mt-1">{error.message || 'An unexpected error occurred in the inspection terminal.'}</p>
        </div>
        <button
          onClick={() => reset()}
          className="inline-flex items-center space-x-2 bg-gov-navy text-white text-xs font-medium px-4 py-2 rounded-gov hover:bg-blue-900 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Operation</span>
        </button>
      </div>
    </div>
  );
}

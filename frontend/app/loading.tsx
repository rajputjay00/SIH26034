import React from 'react';

export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center space-y-3">
        <div className="w-8 h-8 border-3 border-gov-border border-t-gov-primary rounded-full animate-spin"></div>
        <p className="text-xs text-gov-muted">Loading inspection system data...</p>
      </div>
    </div>
  );
}

import React from 'react';
import Link from 'next/link';
import { FileQuestion, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="bg-white border border-gov-border rounded-gov p-6 max-w-md w-full shadow-xs text-center space-y-4">
        <div className="w-10 h-10 bg-gov-pastelBlue text-gov-primary rounded-full flex items-center justify-center mx-auto">
          <FileQuestion className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gov-navy">Resource Not Found</h3>
          <p className="text-xs text-gov-muted mt-1">The requested inspection case, evidence item, or screen does not exist.</p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center space-x-2 bg-gov-navy text-white text-xs font-medium px-4 py-2 rounded-gov hover:bg-blue-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    </div>
  );
}

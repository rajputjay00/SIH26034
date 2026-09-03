import React from 'react';
import { Check, X, AlertTriangle, Clock, CheckCircle2, RefreshCw } from 'lucide-react';

interface BadgeProps {
  status: string;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ status, className = '', size = 'md' }) => {
  const normStatus = (status || '').toUpperCase();
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-[11px]';

  // Determination & Finding statuses with explicit text + icons
  if (normStatus === 'COMPLIANT' || normStatus === 'PASS') {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 ${sizeClasses} ${className}`}>
        <Check className="w-3 h-3 text-emerald-600 stroke-[2.5]" />
        <span>{normStatus === 'PASS' ? 'PASS' : 'COMPLIANT'}</span>
      </span>
    );
  }

  if (normStatus === 'NON_COMPLIANT' || normStatus === 'FAIL') {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-full bg-rose-50 text-rose-800 border border-rose-200 ${sizeClasses} ${className}`}>
        <X className="w-3 h-3 text-rose-600 stroke-[2.5]" />
        <span>{normStatus === 'FAIL' ? 'FAIL' : 'NON-COMPLIANT'}</span>
      </span>
    );
  }

  if (normStatus === 'REQUIRES_REVIEW' || normStatus === 'REVIEW' || normStatus === 'MANUAL_REVIEW') {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-full bg-amber-50 text-amber-900 border border-amber-300 ${sizeClasses} ${className}`}>
        <AlertTriangle className="w-3 h-3 text-amber-600 stroke-[2.5]" />
        <span>{normStatus === 'REQUIRES_REVIEW' ? 'REQUIRES REVIEW' : 'REVIEW'}</span>
      </span>
    );
  }

  if (normStatus === 'FINALISED') {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-full bg-blue-50 text-blue-900 border border-blue-200 ${sizeClasses} ${className}`}>
        <CheckCircle2 className="w-3 h-3 text-blue-600 stroke-[2.5]" />
        <span>FINALISED</span>
      </span>
    );
  }

  if (normStatus === 'PROCESSING') {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-full bg-indigo-50 text-indigo-800 border border-indigo-200 ${sizeClasses} ${className}`}>
        <RefreshCw className="w-3 h-3 text-indigo-600 animate-spin" />
        <span>PROCESSING</span>
      </span>
    );
  }

  if (normStatus === 'PENDING_REVIEW') {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-full bg-orange-50 text-orange-800 border border-orange-200 ${sizeClasses} ${className}`}>
        <Clock className="w-3 h-3 text-orange-600" />
        <span>PENDING REVIEW</span>
      </span>
    );
  }

  if (normStatus === 'PENDING_EVALUATION' || normStatus === 'DRAFT') {
    return (
      <span className={`inline-flex items-center gap-1 font-medium rounded-full bg-slate-100 text-slate-700 border border-slate-300 ${sizeClasses} ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
        <span>{normStatus === 'PENDING_EVALUATION' ? 'PENDING EVALUATION' : 'DRAFT'}</span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center font-medium rounded-full bg-slate-100 text-slate-700 border border-slate-200 ${sizeClasses} ${className}`}>
      {status}
    </span>
  );
};

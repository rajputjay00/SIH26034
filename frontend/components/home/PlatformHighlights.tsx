'use client';

import React from 'react';
import { ShieldCheck, UserCheck, Target, FileCheck, TrendingUp } from 'lucide-react';

const highlights = [
  {
    icon: ShieldCheck,
    title: 'EVIDENCE FIRST',
    description: 'Every inspection backed by verifiable evidence',
  },
  {
    icon: UserCheck,
    title: 'OFFICER DRIVEN',
    description: 'Empower field officers with digital tools',
  },
  {
    icon: Target,
    title: 'DETERMINISTIC COMPLIANCE',
    description: 'Rule-based engine for accurate findings',
  },
  {
    icon: FileCheck,
    title: 'TRANSPARENT & TRACEABLE',
    description: 'End-to-end audit trail and accountability',
  },
  {
    icon: TrendingUp,
    title: 'INSIGHTFUL ANALYTICS',
    description: 'Actionable insights for better decisions',
  },
];

export const PlatformHighlights: React.FC = () => {
  return (
    <section className="bg-white border-y border-nirikshan-border shadow-xs relative z-20">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-5">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 lg:gap-6 divide-y lg:divide-y-0 lg:divide-x divide-slate-100">
          {highlights.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className={`flex items-start space-x-3 pt-3 lg:pt-0 ${idx > 0 ? 'lg:pl-5' : ''}`}
              >
                <div className="w-9 h-9 rounded-brand bg-slate-50 border border-slate-200 flex items-center justify-center text-nirikshan-navy flex-shrink-0">
                  <Icon className="w-4 h-4 text-nirikshan-blue" />
                </div>
                <div className="min-w-0">
                  <div className="text-[11px] font-bold text-nirikshan-navy tracking-tight uppercase">
                    {item.title}
                  </div>
                  <p className="text-[11px] text-slate-500 leading-snug mt-0.5">
                    {item.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

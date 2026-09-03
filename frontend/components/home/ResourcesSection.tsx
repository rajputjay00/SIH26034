'use client';

import React from 'react';
import Link from 'next/link';
import { BookOpen, FileText, Ruler, ShieldCheck, ArrowRight, ExternalLink } from 'lucide-react';

const resources = [
  {
    icon: BookOpen,
    category: 'STATUTORY REFERENCE',
    title: 'Legal Metrology Rules, 2011 Reference',
    desc: 'Statutory guidelines covering Rule 6 mandatory declarations and Rule 7 principal display panel font requirements.',
    badge: 'Statutory Reference',
  },
  {
    icon: Ruler,
    category: 'MEASUREMENT',
    title: 'Calibration Methodology',
    desc: 'Physical coin reference scale factor protocol using standard 23.00mm diameter for millimeter-per-pixel conversion.',
    badge: 'Methodology',
  },
  {
    icon: FileText,
    category: 'FIELD WORKFLOW',
    title: 'Evidence Capture Guide',
    desc: 'Procedures for capturing multi-view packaging panels (Front, Back, Side, Base) with framing and glare checks.',
    badge: 'Field Guide',
  },
  {
    icon: ShieldCheck,
    category: 'INTEGRITY & AUDIT',
    title: 'Report & Verification Guide',
    desc: 'Technical specification for SHA-256 evidence integrity hashing, tamper-detection, and QR verification endpoints.',
    badge: 'Technical Spec',
  },
];

export const ResourcesSection: React.FC = () => {
  return (
    <section className="py-16 bg-nirikshan-lightBg border-b border-nirikshan-border" id="resources">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-4">
          <div>
            <div className="inline-flex items-center space-x-1.5 bg-blue-50 text-nirikshan-blue px-3 py-1 rounded-full text-xs font-semibold border border-blue-200 mb-2">
              <BookOpen className="w-3.5 h-3.5" />
              <span>RESOURCES &amp; GUIDANCE</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-nirikshan-navy tracking-tight">
              Platform Knowledge Base &amp; Methodology
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
              Authoritative technical documentation and field guidelines supporting inspection integrity and enforcement accuracy.
            </p>
          </div>

          <Link
            href="/inspections"
            className="inline-flex items-center space-x-1.5 bg-white border border-slate-200 hover:border-nirikshan-blue text-xs font-semibold px-4 py-2 rounded-brand text-nirikshan-navy hover:text-nirikshan-blue transition-colors shadow-xs self-start md:self-end"
          >
            <span>Launch Inspection Console</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* 4 Resources Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {resources.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="bg-white p-5 rounded-brand border border-slate-200 shadow-xs hover:border-nirikshan-blue/50 hover:shadow-card transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-semibold tracking-wider uppercase text-nirikshan-blue bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {item.badge}
                    </span>
                    <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-nirikshan-navy">
                      <Icon className="w-4 h-4 text-nirikshan-blue" />
                    </div>
                  </div>

                  <div className="text-[10px] font-semibold uppercase text-slate-500 mb-1">
                    {item.category}
                  </div>

                  <h3 className="text-xs font-bold text-nirikshan-navy tracking-tight leading-snug mb-2">
                    {item.title}
                  </h3>

                  <p className="text-xs text-slate-500 leading-relaxed">
                    {item.desc}
                  </p>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-[11px] font-semibold text-nirikshan-navy hover:text-nirikshan-blue cursor-pointer">
                  <span>View Documentation</span>
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

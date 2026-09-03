'use client';

import React from 'react';
import Link from 'next/link';
import {
  Camera,
  ShieldCheck,
  Cpu,
  Scale,
  Ruler,
  FileCheck2,
  ArrowRight,
  Layers,
  Sparkles
} from 'lucide-react';

const capabilities = [
  {
    icon: Camera,
    tag: 'FIELD READY',
    title: 'In-App Camera Capture',
    desc: 'Rear-camera capture with live framing guides, brightness & glare quality checks, retake safeguards, and offline local queuing.',
    link: '/inspections',
  },
  {
    icon: ShieldCheck,
    tag: 'FORENSIC INTEGRITY',
    title: 'Multi-View Evidence Pipeline',
    desc: 'Structured Front, Back, Side, and Base ingestion with server-side authoritative SHA-256 hashing and raw byte immutability.',
    link: '/inspections',
  },
  {
    icon: Cpu,
    tag: 'SPATIAL EXTRACTION',
    title: 'PaddleOCR & Polygon Mapping',
    desc: 'Coordinate-aware text extraction mapping bounding boxes to 8 mandatory declarations with complete visual provenance.',
    link: '/inspections',
  },
  {
    icon: Scale,
    tag: 'DETERMINISTIC',
    title: 'Statutory Compliance Engine',
    desc: 'Rule 6 & Rule 7 PC Rules 2011 compliance evaluation with Decimal-safe Unit Sale Price arithmetic and cross-view validation.',
    link: '/inspections',
  },
  {
    icon: Ruler,
    tag: 'METROLOGY',
    title: 'Physical ₹5 Coin Calibration',
    desc: 'Standard 23.00mm physical coin reference scale factor converting pixel dimensions to statutory millimeter font heights.',
    link: '/inspections',
  },
  {
    icon: FileCheck2,
    tag: 'STATUTORY REPORTS',
    title: 'Forensic PDF & QR Integrity',
    desc: '3-part official inspection reports with cryptographic audit hash chains and public read-only verification endpoints.',
    link: '/inspections',
  },
];

export const CoreCapabilities: React.FC = () => {
  return (
    <section className="py-16 bg-white border-b border-nirikshan-border" id="capabilities">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-4">
          <div>
            <div className="inline-flex items-center space-x-1.5 bg-slate-100 text-nirikshan-navy px-3 py-1 rounded-full text-xs font-semibold border border-slate-200 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-nirikshan-saffron" />
              <span>CORE CAPABILITIES</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-nirikshan-navy tracking-tight">
              Engineered for Authoritative Enforcement
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
              Comprehensive decision-support tools built to empower legal metrology officers in the field and at the review desk.
            </p>
          </div>

          <Link
            href="/inspections"
            className="inline-flex items-center space-x-1 text-xs font-semibold text-nirikshan-blue hover:text-nirikshan-navy transition-colors self-start md:self-end"
          >
            <span>View All Inspection Cases</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* 6 Capabilities Grid (Varied composition) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {capabilities.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="group bg-slate-50/70 hover:bg-white p-6 rounded-brand border border-slate-200 hover:border-nirikshan-blue/50 shadow-xs hover:shadow-card transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-brand bg-white border border-slate-200 group-hover:border-blue-200 flex items-center justify-center text-nirikshan-navy group-hover:text-nirikshan-blue shadow-xs transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-semibold tracking-wider uppercase text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                      {item.tag}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-nirikshan-navy tracking-tight mb-2">
                    {item.title}
                  </h3>

                  <p className="text-xs text-slate-600 leading-relaxed">
                    {item.desc}
                  </p>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-200/60 flex items-center justify-between">
                  <Link
                    href={item.link}
                    className="inline-flex items-center space-x-1 text-[11px] font-semibold text-nirikshan-blue hover:text-nirikshan-navy transition-colors"
                  >
                    <span>Launch Module</span>
                    <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

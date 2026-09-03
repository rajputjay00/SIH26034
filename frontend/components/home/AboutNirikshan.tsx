'use client';

import React from 'react';
import Link from 'next/link';
import { Package, Camera, Cpu, Scale, UserCheck, FileText, ArrowRight } from 'lucide-react';

const steps = [
  { step: '01', title: 'PRODUCT', desc: 'Packaged commodity intake', icon: Package },
  { step: '02', title: 'EVIDENCE', desc: 'Multi-view SHA-256 capture', icon: Camera },
  { step: '03', title: 'OCR', desc: 'PaddleOCR polygon extraction', icon: Cpu },
  { step: '04', title: 'ASSESSMENT', desc: 'Deterministic rule engine', icon: Scale },
  { step: '05', title: 'REVIEW', desc: 'Officer review & correction', icon: UserCheck },
  { step: '06', title: 'REPORT', desc: 'Forensic PDF & QR verify', icon: FileText },
];

export const AboutNirikshan: React.FC = () => {
  return (
    <section className="py-16 bg-nirikshan-lightBg border-b border-nirikshan-border" id="about">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-12">
          <div className="inline-flex items-center space-x-1.5 bg-blue-50 text-nirikshan-blue px-3 py-1 rounded-full text-xs font-semibold border border-blue-200">
            <span>ABOUT NIRIKSHAN</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-nirikshan-navy tracking-tight">
            A Smarter Way to Conduct Digital Inspections
          </h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            NIRIKSHAN transforms the legal metrology inspection lifecycle into an evidence-oriented, verifiable workflow. It bridges field physical capture, computer vision extraction, deterministic statutory evaluation, and officer adjudication.
          </p>
        </div>

        {/* 6-Step Visual Process Stream */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 relative">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="bg-white p-4 rounded-brand border border-slate-200 shadow-xs hover:border-nirikshan-blue/40 hover:shadow-card transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-semibold text-nirikshan-saffron bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      {item.step}
                    </span>
                    <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-nirikshan-navy">
                      <Icon className="w-4 h-4 text-nirikshan-blue" />
                    </div>
                  </div>
                  <h3 className="text-xs font-bold text-nirikshan-navy tracking-tight uppercase mb-1">
                    {item.title}
                  </h3>
                  <p className="text-[11px] text-slate-500 leading-snug">
                    {item.desc}
                  </p>
                </div>

                {idx < steps.length - 1 && (
                  <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 text-slate-300 z-10">
                    {/* Flow arrow handled visually */}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Action Button */}
        <div className="mt-10 text-center">
          <Link
            href="/inspections"
            className="inline-flex items-center space-x-2 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-xs font-semibold px-5 py-2.5 rounded-brand transition-colors shadow-xs"
          >
            <span>Explore Inspection Console</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </section>
  );
};

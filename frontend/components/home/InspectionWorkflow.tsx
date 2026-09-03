'use client';

import React from 'react';
import { Camera, CheckCircle2, Cpu, Scale, UserCheck, FileText } from 'lucide-react';

const workflowSteps = [
  {
    step: '01',
    title: 'CAPTURE',
    tagline: 'Field Ingestion',
    desc: 'Multi-view capture of Front, Back, Side, and Base with in-app framing guides and offline queuing.',
    icon: Camera,
  },
  {
    step: '02',
    title: 'VERIFY',
    tagline: 'Quality Gate & Hash',
    desc: 'Server calculates authoritative SHA-256 hash; OpenCV checks Laplacian blur, glare, and contrast.',
    icon: CheckCircle2,
  },
  {
    step: '03',
    title: 'EXTRACT',
    tagline: 'PaddleOCR & Normalization',
    desc: 'Coordinate polygons map to MRP, Net Quantity, USP, Manufacturer, Origin, and Date declarations.',
    icon: Cpu,
  },
  {
    step: '04',
    title: 'ASSESS',
    tagline: 'Deterministic Rules',
    desc: 'Pure rule engine evaluates Rule 6 mandatory declarations, USP math, and Rule 7 PDP font heights.',
    icon: Scale,
  },
  {
    step: '05',
    title: 'REVIEW',
    tagline: 'Officer Adjudication',
    desc: 'Officer reviews findings, audits corrections, acknowledges signals, and enters statutory decision.',
    icon: UserCheck,
  },
  {
    step: '06',
    title: 'REPORT',
    tagline: 'Forensic PDF & QR',
    desc: 'ReportLab generates 3-part forensic report with tamper-evident QR code and cryptographic audit chain.',
    icon: FileText,
  },
];

export const InspectionWorkflow: React.FC = () => {
  return (
    <section className="py-16 bg-nirikshan-lightBg border-b border-nirikshan-border" id="workflow">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-14">
          <div className="inline-flex items-center space-x-1.5 bg-amber-50 text-nirikshan-saffron px-3 py-1 rounded-full text-xs font-semibold border border-amber-200">
            <span>END-TO-END METHODOLOGY</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-nirikshan-navy tracking-tight">
            From Capture to Compliance
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
            A continuous, audited 6-phase journey ensuring every statutory determination is grounded in verifiable physical evidence.
          </p>
        </div>

        {/* Timeline (Desktop: Horizontal with connector, Mobile: Vertical) */}
        <div className="relative">
          {/* Connecting Line (Desktop) */}
          <div className="hidden lg:block absolute top-12 left-8 right-8 h-0.5 bg-slate-200 z-0"></div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 relative z-10">
            {workflowSteps.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="bg-white p-5 rounded-brand border border-slate-200 shadow-xs hover:shadow-card hover:border-nirikshan-blue/50 transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* Step Badge & Icon */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-10 h-10 rounded-full bg-slate-50 border-2 border-nirikshan-saffron/40 flex items-center justify-center text-nirikshan-navy font-bold text-xs shadow-xs">
                        <Icon className="w-4 h-4 text-nirikshan-navy" />
                      </div>
                      <span className="text-xs font-bold text-nirikshan-saffron">
                        {item.step}
                      </span>
                    </div>

                    <div className="text-[10px] font-semibold tracking-wider uppercase text-nirikshan-blue mb-1">
                      {item.tagline}
                    </div>

                    <h3 className="text-sm font-bold text-nirikshan-navy tracking-tight uppercase mb-2">
                      {item.title}
                    </h3>

                    <p className="text-xs text-slate-500 leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

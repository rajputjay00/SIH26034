'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-nirikshan-navy text-slate-300 pt-12 pb-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        {/* Main 4-Column Responsive HTML/CSS Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-8 pb-10 border-b border-slate-700/60">
          {/* Column 1: Brand Logo & Institutional Description (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="relative h-11 w-60">
              <Image
                src="/assets/branding/nirikshan-logo-white.svg"
                alt="NIRIKSHAN — Legal Metrology Compliance & Inspection System"
                fill
                className="object-contain object-left"
              />
            </div>
            
            <p className="text-xs text-slate-300 leading-relaxed pr-6">
              An evidence-oriented digital inspection and decision-support terminal built for structured declaration verification of packaged commodities under the Legal Metrology (Packaged Commodities) Rules, 2011.
            </p>
          </div>

          {/* Column 2: Platform Links (2 cols) */}
          <div className="lg:col-span-2 space-y-3">

            <h4 className="text-xs font-bold uppercase tracking-wider text-white border-b border-slate-700 pb-1.5 inline-block">
              Platform
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/inspections" className="hover:text-white transition-colors">
                  Inspections
                </Link>
              </li>
              <li>
                <Link href="/inspections" className="hover:text-white transition-colors">
                  Evidence
                </Link>
              </li>
              <li>
                <Link href="/inspections" className="hover:text-white transition-colors">
                  Compliance
                </Link>
              </li>
              <li>
                <Link href="/inspections" className="hover:text-white transition-colors">
                  Reports
                </Link>
              </li>
              <li>
                <Link href="/" className="hover:text-white transition-colors">
                  Analytics
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Resources (3 cols) */}
          <div className="lg:col-span-3 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-white border-b border-slate-700 pb-1.5 inline-block">
              Resources
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#resources" className="hover:text-white transition-colors">
                  Documentation
                </a>
              </li>
              <li>
                <a href="#resources" className="hover:text-white transition-colors">
                  Inspection Guide
                </a>
              </li>
              <li>
                <a href="#resources" className="hover:text-white transition-colors">
                  Calibration Methodology
                </a>
              </li>
              <li>
                <a href="#resources" className="hover:text-white transition-colors">
                  FAQ &amp; Support
                </a>
              </li>
            </ul>
          </div>

          {/* Column 4: Legal & Policy (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-white border-b border-slate-700 pb-1.5 inline-block">
              Legal
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#resources" className="hover:text-white transition-colors">
                  Privacy
                </a>
              </li>
              <li>
                <a href="#resources" className="hover:text-white transition-colors">
                  Accessibility
                </a>
              </li>
              <li>
                <a href="#resources" className="hover:text-white transition-colors">
                  Terms of Use
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar: Copyright & System Identity */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div>
            © {new Date().getFullYear()} <strong>NIRIKSHAN</strong> • Legal Metrology Compliance &amp; Inspection System
          </div>
          <div className="text-[11px] text-slate-500">
            Evidence-Oriented Decision Support Terminal
          </div>
        </div>
      </div>
    </footer>
  );
};

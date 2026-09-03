'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, CheckSquare, History, ShieldAlert, FileText, Settings, ShieldCheck } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    { label: 'Executive Dashboard', href: '/', icon: LayoutDashboard },
    { label: 'Officer Review & History', href: '/inspections', icon: History },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gov-border flex flex-col justify-between h-[calc(100vh-61px)] p-4 shadow-xs">
      <div className="space-y-4">
        <div>
          <div className="px-3 py-1.5 text-[10px] font-bold text-gov-muted uppercase tracking-wider">
            Enforcement Portal
          </div>
          <nav className="space-y-1 mt-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-gov text-xs transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-900 font-semibold border border-blue-200'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-gov-primary' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="pt-2 border-t border-slate-100">
          <div className="px-3 py-1.5 text-[10px] font-bold text-gov-muted uppercase tracking-wider">
            Public Access
          </div>
          <div className="space-y-1 mt-1">
            <Link
              href="/verify/audit"
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-gov text-xs text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <ShieldCheck className="w-4 h-4 text-slate-400" />
              <span>QR Report Verification</span>
            </Link>
          </div>
        </div>
      </div>

      <div className="p-3 bg-slate-50 rounded-gov border border-slate-200 text-[11px] text-slate-500 space-y-1">
        <div className="font-semibold text-slate-800">NIRIKSHAN Terminal</div>
        <div className="text-[10px] text-slate-600">Legal Metrology PC Rules, 2011</div>
        <div className="text-[10px] text-blue-700 font-medium">Rule Pack: v1.0.0 Active</div>
      </div>
    </aside>
  );
};

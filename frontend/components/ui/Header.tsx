import React from 'react';
import { ShieldCheck, User, Activity } from 'lucide-react';

interface HeaderProps {
  officerName?: string;
  badgeNumber?: string;
  systemStatus?: string;
}

export const Header: React.FC<HeaderProps> = ({
  officerName = "Inspector R. K. Sharma",
  badgeNumber = "LM-DEL-4092",
  systemStatus = "ONLINE"
}) => {
  return (
    <header className="bg-white border-b border-gov-border px-6 py-3 flex items-center justify-between shadow-xs">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-gov bg-gov-navy flex items-center justify-center text-white">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-semibold text-gov-navy tracking-tight">
            LegalMetriX
          </h1>
          <p className="text-xs text-gov-muted">
            Legal Metrology Packaged Commodity Inspection Terminal
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2 text-xs text-gov-muted bg-gov-pastelGreen px-3 py-1.5 rounded-gov border border-green-200">
          <Activity className="w-3.5 h-3.5 text-green-600" />
          <span className="font-medium text-green-800">System: {systemStatus}</span>
        </div>

        <div className="flex items-center space-x-3 border-l border-gov-border pl-6">
          <div className="w-8 h-8 rounded-full bg-gov-pastelBlue flex items-center justify-center text-gov-primary border border-blue-200">
            <User className="w-4 h-4" />
          </div>
          <div className="text-left">
            <div className="text-xs font-semibold text-gov-text">{officerName}</div>
            <div className="text-[11px] mono-code text-gov-muted">{badgeNumber}</div>
          </div>
        </div>
      </div>
    </header>
  );
};

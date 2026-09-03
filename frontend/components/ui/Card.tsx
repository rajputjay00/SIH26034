import React from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ title, subtitle, action, children, className = '' }) => {
  return (
    <div className={`bg-white border border-gov-border rounded-gov p-5 shadow-xs ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-gov-border pb-3 mb-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-gov-navy tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-gov-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};

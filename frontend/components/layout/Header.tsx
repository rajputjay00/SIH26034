'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import {
  Search,
  User,
  ShieldCheck,
  Menu,
  X,
  ChevronDown,
  HelpCircle,
  Eye,
  Globe,
  LogIn,
  CheckCircle2,
  AlertCircle,
  Camera,
  Plus,
  RefreshCw,
  FolderPlus
} from 'lucide-react';
import { fetchHealth, createInspectionCase } from '../../lib/api';

export const Header: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [resourcesOpen, setResourcesOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [systemHealth, setSystemHealth] = useState<'ONLINE' | 'DEGRADED' | 'CHECKING'>('CHECKING');
  const [authUser, setAuthUser] = useState<{ name: string; role: string } | null>(null);
  
  // Quick New Inspection Modal State
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [caseNotes, setCaseNotes] = useState('');
  const [creatingCase, setCreatingCase] = useState(false);

  useEffect(() => {
    // Check real backend health
    fetchHealth()
      .then((data) => {
        if (data.status === 'HEALTHY' || data.status === 'ok') {
          setSystemHealth('ONLINE');
        } else {
          setSystemHealth('DEGRADED');
        }
      })
      .catch(() => {
        setSystemHealth('DEGRADED');
      });

    // Check if real auth token / user is stored
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      const storedRole = localStorage.getItem('role') || 'OFFICER';
      const storedUser = localStorage.getItem('user_id');
      if (token && storedUser) {
        setAuthUser({ name: storedUser, role: storedRole });
      } else {
        setAuthUser(null);
      }
    }
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
    setResourcesOpen(false);
  }, [pathname]);

  const handleQuickCreateCase = async () => {
    try {
      setCreatingCase(true);
      const created = await createInspectionCase(caseNotes || 'Packaged commodity sample inspection');
      setShowNewCaseModal(false);
      setCaseNotes('');
      router.push(`/cases/${created.inspection_id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Case creation failed';
      alert(message);
    } finally {
      setCreatingCase(false);
    }
  };

  const navItems = [
    { name: 'Home', href: '/' },
    { name: 'Inspections', href: '/inspections' },
    { name: 'Reports', href: '/inspections' },
    { name: 'Resources', href: '#resources' },
  ];

  const resourcesDropdown = [
    { name: 'Inspection Workflow', href: '#resources', desc: 'Standard operating procedures for field verification' },
    { name: 'Calibration Methodology', href: '#resources', desc: 'Physical coin reference scale factor protocol' },
    { name: 'Evidence Capture Guide', href: '#resources', desc: 'Multi-view packaging inspection standards' },
    { name: 'Report & Verification Guide', href: '#resources', desc: 'Cryptographic SHA-256 and QR verification' },
  ];

  const isNavActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <header className="w-full sticky top-0 z-40 bg-white shadow-xs border-b border-nirikshan-border/80">
      {/* 1. TOP UTILITY BAR */}
      <div className="bg-nirikshan-navy text-white text-[11px] px-4 md:px-8 py-1.5 flex items-center justify-between border-b border-nirikshan-navyDark/50">
        <div className="flex items-center space-x-3">
          <span className="font-semibold tracking-wider text-nirikshan-saffron">NIRIKSHAN</span>
          <span className="text-slate-400 hidden sm:inline">•</span>
          <span className="text-slate-300 hidden sm:inline font-medium">
            Legal Metrology Compliance &amp; Inspection System
          </span>
        </div>

        <div className="flex items-center space-x-4 text-slate-300">
          <a
            href="#resources"
            className="hover:text-white flex items-center space-x-1 transition-colors"
          >
            <HelpCircle className="w-3 h-3 text-nirikshan-saffron" />
            <span className="hidden xs:inline">Help &amp; Support</span>
          </a>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1 hover:text-white cursor-pointer transition-colors" title="High-contrast institutional view">
            <Eye className="w-3 h-3 text-blue-400" />
            <span className="hidden xs:inline">Accessibility</span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1 text-slate-200">
            <Globe className="w-3 h-3 text-emerald-400" />
            <span>English</span>
          </div>
        </div>
      </div>

      {/* 2. MAIN HEADER (Logo + Search + Real Status + Primary Actions) */}
      <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-8 py-2.5 sm:py-3 flex items-center justify-between gap-2 sm:gap-4">
        {/* Left: Brand Logo */}
        <Link href="/" className="flex items-center space-x-2 group shrink-0">
          <div className="relative h-9 w-36 xs:h-10 xs:w-48 sm:h-11 sm:w-60 md:h-12 md:w-72">
            <Image
              src="/assets/branding/nirikshan-logo.svg"
              alt="NIRIKSHAN — Legal Metrology Compliance & Inspection System"
              fill
              className="object-contain object-left"
              priority
            />
          </div>
        </Link>

        {/* Center: Quick Search Bar (Desktop) */}
        <div className="hidden lg:flex items-center flex-1 max-w-md mx-4">
          <div className="relative w-full">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Case Number or Commodity..."
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-brand text-nirikshan-navy placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-nirikshan-blue/30 focus:border-nirikshan-blue transition-all"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        {/* Right: Actions, Health Status & User Profile */}
        <div className="flex items-center space-x-1.5 sm:space-x-3 shrink-0">
          {/* Live System Health Pill */}
          {systemHealth === 'ONLINE' ? (
            <div className="hidden xl:flex items-center space-x-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 rounded-brand text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Online</span>
            </div>
          ) : systemHealth === 'DEGRADED' ? (
            <div className="hidden xl:flex items-center space-x-1.5 bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-1 rounded-brand text-xs font-medium">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              <span>Offline</span>
            </div>
          ) : null}

          {/* Primary Action Button 1: Start New Inspection */}
          <button
            onClick={() => setShowNewCaseModal(true)}
            className="inline-flex items-center space-x-1 sm:space-x-1.5 bg-nirikshan-saffron hover:bg-nirikshan-saffron/90 text-white text-[11px] sm:text-xs font-bold px-2.5 sm:px-3 py-1.5 rounded-brand transition-all shadow-xs"
          >
            <Plus className="w-3.5 h-3.5 shrink-0" />
            <span className="hidden sm:inline">+ Start Inspection</span>
            <span className="sm:hidden">+ New</span>
          </button>

          {/* Primary Action Button 2: Console (Hidden on ultra-small screens, in drawer) */}
          <Link
            href="/inspections"
            className="hidden xs:inline-flex items-center space-x-1.5 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-[11px] sm:text-xs font-semibold px-2.5 sm:px-3 py-1.5 rounded-brand transition-colors shadow-xs"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-blue-300" />
            <span className="hidden sm:inline">Review Desk</span>
            <span className="sm:hidden">Desk</span>
          </Link>

          {/* User Profile or Sign In */}
          {authUser ? (
            <div className="hidden sm:flex items-center space-x-2 pl-2 sm:pl-3 border-l border-slate-200">
              <div className="w-7 h-7 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-nirikshan-navy">
                <User className="w-3.5 h-3.5" />
              </div>
              <div className="hidden md:block text-left leading-tight">
                <div className="text-xs font-semibold text-nirikshan-navy">{authUser.name}</div>
                <div className="text-[10px] font-medium text-slate-500">{authUser.role}</div>
              </div>
            </div>
          ) : (
            <Link
              href="/inspections"
              className="hidden sm:inline-flex items-center space-x-1 bg-slate-100 hover:bg-slate-200 text-nirikshan-navy text-xs font-semibold px-2.5 py-1.5 rounded-brand transition-colors border border-slate-300"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </Link>
          )}

          {/* Mobile Menu Hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-1.5 text-slate-600 hover:text-nirikshan-navy rounded-md hover:bg-slate-100 transition-colors"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5 text-nirikshan-navy" /> : <Menu className="w-5 h-5 text-nirikshan-navy" />}
          </button>
        </div>
      </div>

      {/* 3. PRIMARY NAVIGATION BAR */}
      <nav className="bg-slate-50/80 border-t border-slate-200/80 px-4 md:px-8 hidden lg:block">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <ul className="flex items-center space-x-1 text-xs font-medium text-slate-700">
            {navItems.map((item) => {
              const active = isNavActive(item.href);
              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className={`inline-flex items-center px-3.5 py-2.5 border-b-2 font-semibold transition-all ${
                      active
                        ? 'border-nirikshan-saffron text-nirikshan-navy bg-white/70 shadow-xs'
                        : 'border-transparent text-slate-600 hover:text-nirikshan-navy hover:border-slate-300'
                    }`}
                  >
                    {item.name}
                  </Link>
                </li>
              );
            })}

            {/* Resources Dropdown */}
            <li className="relative">
              <button
                onClick={() => setResourcesOpen(!resourcesOpen)}
                onBlur={() => setTimeout(() => setResourcesOpen(false), 200)}
                className="inline-flex items-center space-x-1 px-3.5 py-2.5 border-b-2 border-transparent font-semibold text-slate-600 hover:text-nirikshan-navy hover:border-slate-300 transition-all"
              >
                <span>Guidelines</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${resourcesOpen ? 'rotate-180' : ''}`} />
              </button>

              {resourcesOpen && (
                <div className="absolute left-0 mt-1 w-72 bg-white rounded-brand shadow-elevated border border-slate-200 py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
                  {resourcesDropdown.map((res) => (
                    <a
                      key={res.name}
                      href={res.href}
                      className="block px-4 py-2 hover:bg-slate-50 transition-colors"
                    >
                      <div className="text-xs font-semibold text-nirikshan-navy">{res.name}</div>
                      <div className="text-[11px] text-slate-500">{res.desc}</div>
                    </a>
                  ))}
                </div>
              )}
            </li>
          </ul>

          <div className="text-xs font-medium text-slate-500">
            Legal Metrology Enforcement System
          </div>
        </div>
      </nav>


      {/* MOBILE DRAWER */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white border-t border-slate-200 px-4 py-4 space-y-3 shadow-lg animate-in slide-in-from-top duration-200">
          <div className="space-y-2">
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                setShowNewCaseModal(true);
              }}
              className="w-full flex items-center justify-center space-x-2 bg-nirikshan-saffron text-white text-xs font-bold py-2.5 rounded-brand shadow-xs"
            >
              <Plus className="w-4 h-4" />
              <span>+ Start New Inspection</span>
            </button>

            <Link
              href="/inspections"
              className="w-full flex items-center justify-center space-x-2 bg-nirikshan-navy text-white text-xs font-semibold py-2.5 rounded-brand"
            >
              <ShieldCheck className="w-4 h-4 text-blue-300" />
              <span>Open Officer Review Desk</span>
            </Link>
          </div>

          <div className="space-y-1 pt-2 border-t border-slate-100">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="block px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-nirikshan-navy"
              >
                {item.name}
              </Link>
            ))}
            <a
              href="#resources"
              className="block px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-nirikshan-navy"
            >
              Guidelines &amp; Methodology
            </a>
          </div>
        </div>
      )}

      {/* GLOBAL START NEW INSPECTION MODAL */}
      {showNewCaseModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-brand max-w-md w-full p-6 shadow-elevated border border-slate-200">
            <div className="flex items-center space-x-2 text-nirikshan-navy mb-2">
              <div className="w-7 h-7 rounded-full bg-blue-50 flex items-center justify-center text-nirikshan-blue">
                <FolderPlus className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold">
                Start New Inspection Case
              </h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Initialize a new packaged commodity verification record. You will be taken directly to the evidence capture workbench to photograph product panels.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-nirikshan-navy mb-1">
                  Commodity Sample Description / Notes
                </label>
                <textarea
                  value={caseNotes}
                  onChange={(e) => setCaseNotes(e.target.value)}
                  placeholder="e.g. 500g Whole Wheat Flour packet sampled from Retail Mart"
                  className="w-full text-xs p-3 border border-slate-200 rounded-brand focus:ring-2 focus:ring-nirikshan-blue/30 focus:border-nirikshan-blue outline-hidden"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowNewCaseModal(false)}
                className="px-4 py-2 border border-slate-200 text-slate-600 text-xs font-semibold rounded-brand hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleQuickCreateCase}
                disabled={creatingCase}
                className="px-4 py-2 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-xs font-bold rounded-brand transition-colors flex items-center space-x-1.5 shadow-xs"
              >
                {creatingCase ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Camera className="w-3.5 h-3.5 text-nirikshan-saffron" />}
                <span>Initialize &amp; Capture Photo</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

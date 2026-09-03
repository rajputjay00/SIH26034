'use client';

import React from 'react';
import { HeroCarousel } from '../components/home/HeroCarousel';
import { PlatformHighlights } from '../components/home/PlatformHighlights';
import { AboutNirikshan } from '../components/home/AboutNirikshan';
import { CoreCapabilities } from '../components/home/CoreCapabilities';
import { InspectionWorkflow } from '../components/home/InspectionWorkflow';
import { EvidenceSection } from '../components/home/EvidenceSection';
import { ComplianceIntelligence } from '../components/home/ComplianceIntelligence';
import { LiveActivityQueues } from '../components/home/LiveActivityQueues';
import { ResourcesSection } from '../components/home/ResourcesSection';

export default function HomePage() {
  return (
    <div className="w-full bg-white flex flex-col min-h-screen">
      {/* 1. HERO CAROUSEL */}
      <HeroCarousel />

      {/* 2. PLATFORM HIGHLIGHTS STRIP */}
      <PlatformHighlights />

      {/* 3. ABOUT NIRIKSHAN */}
      <AboutNirikshan />

      {/* 4. CORE CAPABILITIES */}
      <CoreCapabilities />

      {/* 5. INSPECTION WORKFLOW TIMELINE */}
      <InspectionWorkflow />

      {/* 6. EVIDENCE & TRACEABILITY */}
      <EvidenceSection />

      {/* 7. COMPLIANCE INTELLIGENCE */}
      <ComplianceIntelligence />

      {/* 8. LIVE ACTIVITY & REVIEW QUEUES */}
      <LiveActivityQueues />

      {/* 9. RESOURCES & GUIDANCE */}
      <ResourcesSection />
    </div>
  );
}

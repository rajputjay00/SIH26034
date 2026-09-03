import React from 'react';
import { Inter } from 'next/font/google';
import './globals.css';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import { NetworkStatusBanner } from '../components/ui/NetworkStatusBanner';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata = {
  title: 'NIRIKSHAN — Legal Metrology Compliance & Inspection System',
  description: 'Evidence-oriented packaged commodity legal metrology inspection and decision-support terminal.',
  icons: {
    icon: '/assets/branding/nirikshan-mark.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`scroll-smooth ${inter.variable}`}>
      <body className={`${inter.className} bg-nirikshan-lightBg min-h-screen flex flex-col font-sans antialiased text-nirikshan-navy selection:bg-nirikshan-saffron selection:text-white`}>
        {/* Institutional Header with Utility Bar & Navigation */}
        <Header />
        
        {/* Offline / Online Sync Queue Status Bar */}
        <NetworkStatusBanner />

        {/* Full-width Main Content Area */}
        <main className="flex-1 w-full">
          {children}
        </main>

        {/* Institutional Footer */}
        <Footer />
      </body>
    </html>
  );
}

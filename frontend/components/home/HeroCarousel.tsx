'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Image from 'next/image';
import { ChevronLeft, ChevronRight, Play, Pause } from 'lucide-react';

interface SlideData {
  id: number;
  stage: string;
  imageSrc: string;
  alt: string;
}

const slides: SlideData[] = [
  {
    id: 1,
    stage: 'INSPECT',
    imageSrc: '/assets/banners/banner-01.png',
    alt: 'Nirikshan Inspect: 5-Step Process Flow (Capture, Verify, Assess, Record, Analyze)',
  },
  {
    id: 2,
    stage: 'VERIFY',
    imageSrc: '/assets/banners/banner-02.png',
    alt: 'Nirikshan Verify: Field Inspection & Label Declaration Verification',
  },
  {
    id: 3,
    stage: 'ASSESS',
    imageSrc: '/assets/banners/banner-03.png',
    alt: 'Nirikshan Assess: Precision in Every Inspection & Compliance Decision Support',
  },
];

export const HeroCarousel: React.FC = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const nextSlide = useCallback(() => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
  }, []);

  const prevSlide = useCallback(() => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
  }, []);

  // 5-second automatic rotation across the 3 uploaded banners
  useEffect(() => {
    if (isPaused) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = setInterval(() => {
      nextSlide();
    }, 5000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPaused, nextSlide]);

  // Pause when document is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPaused(document.hidden);
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight') nextSlide();
    if (e.key === 'ArrowLeft') prevSlide();
  };

  // Touch swipe support for mobile
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStart === null) return;
    const touchEnd = e.changedTouches[0].clientX;
    const diff = touchStart - touchEnd;
    if (diff > 50) nextSlide();
    if (diff < -50) prevSlide();
    setTouchStart(null);
  };

  return (
    <section
      className="relative w-full bg-slate-900 overflow-hidden select-none focus:outline-none"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onFocus={() => setIsPaused(true)}
      onBlur={() => setIsPaused(false)}
      onKeyDown={handleKeyDown}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      tabIndex={0}
      aria-label="Nirikshan 3-Stage Carousel"
    >
      {/* 16:9 Aspect Ratio Container */}
      <div className="relative w-full aspect-[16/9] max-h-[560px] min-h-[260px]">
        {slides.map((slide, index) => {
          const isActive = index === currentSlide;
          return (
            <div
              key={slide.id}
              className={`absolute inset-0 transition-opacity duration-700 ease-in-out ${
                isActive ? 'opacity-100 z-10' : 'opacity-0 z-0 pointer-events-none'
              }`}
            >
              <Image
                src={slide.imageSrc}
                alt={slide.alt}
                fill
                priority={index === 0}
                className="object-cover object-center"
              />
            </div>
          );
        })}

        {/* Previous Button */}
        <button
          onClick={prevSlide}
          className="absolute left-3 md:left-6 top-1/2 -translate-y-1/2 z-20 w-9 h-9 md:w-11 md:h-11 rounded-full bg-black/40 hover:bg-black/70 text-white backdrop-blur-md flex items-center justify-center border border-white/20 transition-all transform hover:scale-105"
          aria-label="Previous Banner"
        >
          <ChevronLeft className="w-5 h-5 md:w-6 md:h-6" />
        </button>

        {/* Next Button */}
        <button
          onClick={nextSlide}
          className="absolute right-3 md:right-6 top-1/2 -translate-y-1/2 z-20 w-9 h-9 md:w-11 md:h-11 rounded-full bg-black/40 hover:bg-black/70 text-white backdrop-blur-md flex items-center justify-center border border-white/20 transition-all transform hover:scale-105"
          aria-label="Next Banner"
        >
          <ChevronRight className="w-5 h-5 md:w-6 md:h-6" />
        </button>

        {/* Floating Indicator Dots for exactly 3 slides & Pause Toggle */}
        <div className="absolute bottom-4 md:bottom-6 left-1/2 -translate-x-1/2 z-20 flex items-center space-x-2 bg-black/50 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-white/20">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentSlide(i)}
              className={`transition-all rounded-full ${
                i === currentSlide
                  ? 'w-6 h-2 bg-nirikshan-saffron'
                  : 'w-2 h-2 bg-white/60 hover:bg-white'
              }`}
              aria-label={`Go to slide ${i + 1}`}
            />
          ))}

          <span className="text-white/40 text-xs pl-1">|</span>
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="text-white/80 hover:text-white pl-1"
            title={isPaused ? 'Resume rotation' : 'Pause rotation'}
          >
            {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
          </button>
        </div>
      </div>
    </section>
  );
};

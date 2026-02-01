"use client";

import { useEffect, useState } from 'react';

interface ParallaxProviderProps {
  children: React.ReactNode;
}

export default function ParallaxProvider({ children }: ParallaxProviderProps) {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    // Parallax effect for hero background only
    const heroBg = document.querySelector('.parallax-hero-bg');
    if (heroBg) {
      const speed = 0.5;
      heroBg.setAttribute('style', `transform: translateY(${scrollY * speed}px)`);
    }

    // Parallax for specific floating elements (excluding navigation)
    const floatingElements = document.querySelectorAll('.parallax-element');
    floatingElements.forEach((el, index) => {
      const speed = 0.2 + (index * 0.1);
      el.setAttribute('style', `transform: translateY(${scrollY * speed}px)`);
    });

    // Scroll-triggered animations
    const animateElements = document.querySelectorAll('.scroll-animate');
    animateElements.forEach((element) => {
      const elementTop = element.getBoundingClientRect().top;
      const elementBottom = element.getBoundingClientRect().bottom;
      
      if (elementTop < window.innerHeight && elementBottom > 0) {
        element.classList.add('visible');
      }
    });
  }, [scrollY]);

  return <>{children}</>;
}

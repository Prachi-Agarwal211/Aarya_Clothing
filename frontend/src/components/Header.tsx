"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { Search, ShoppingBag, Menu, X, User } from "lucide-react";

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "Cord Sets", href: "/categories/cord-sets" },
    { name: "Gowns", href: "/categories/gowns" },
    { name: "Duppatas", href: "/categories/duppatas" },
    { name: "Kurtis", href: "/categories/kurtis" },
    { name: "Sarees", href: "/categories/sarees" },
    { name: "Kurtis Set", href: "/categories/kurti-set" }, // Re-added as per general navigation needs, or user might want it visible
  ];

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "glass-header py-3" : "bg-transparent py-5"
          }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 text-[#EAEAEA] hover:text-[#C9A227] transition-colors"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Desktop Navigation (Left) */}
            <nav className="hidden md:flex items-center space-x-6 lg:space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  href={link.href}
                  className="text-sm font-medium text-[#EAEAEA] hover:text-[#C9A227] transition-colors tracking-wide"
                >
                  {link.name}
                </Link>
              ))}
            </nav>

            {/* Empty Center (Logo Removed) */}
            <div className="hidden md:block"></div>

            {/* Icons (Right) */}
            <div className="flex items-center space-x-4">
              <button className="p-2 text-[#EAEAEA] hover:text-[#C9A227] transition-colors">
                <Search className="w-5 h-5" />
              </button>
              <Link href="/login" className="p-2 text-[#EAEAEA] hover:text-[#C9A227] transition-colors hidden sm:block">
                <User className="w-5 h-5" />
              </Link>
              <button className="p-2 text-[#EAEAEA] hover:text-[#C9A227] transition-colors relative">
                <ShoppingBag className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-[#C9A227] rounded-full"></span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)}></div>
          <div className="relative w-4/5 max-w-xs bg-[#151517] h-full shadow-2xl p-6 flex flex-col">
            <div className="flex justify-between items-center mb-8">
              <div className="w-6"></div> {/* Spacer since title is removed */}
              <button onClick={() => setMobileMenuOpen(false)} className="text-[#EAEAEA] hover:text-[#C9A227]">
                <X className="w-6 h-6" />
              </button>
            </div>
            <nav className="space-y-6">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  href={link.href}
                  className="block text-lg font-medium text-[#EAEAEA] hover:text-[#C9A227] transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.name}
                </Link>
              ))}
            </nav>
            <div className="mt-auto pt-8 border-t border-[#262626]">
              <Link href="/login" className="flex items-center gap-3 text-[#EAEAEA] hover:text-[#C9A227] transition-colors mb-4">
                <User className="w-5 h-5" />
                <span>Account</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

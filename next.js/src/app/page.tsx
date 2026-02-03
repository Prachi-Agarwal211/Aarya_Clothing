"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { Search, User, ShoppingBag, Menu, X, Truck, Shield, Gift, LogOut } from "lucide-react";
import ParallaxProvider from "./components/ParallaxProvider";

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [navVisible, setNavVisible] = useState(true);
  const [categoriesDropdownOpen, setCategoriesDropdownOpen] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, []);

  // Auto-hide navigation on scroll
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Hide navigation when scrolling down, show when scrolling up
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        setNavVisible(false);
      } else {
        setNavVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    setCurrentUser(null);
  };

  // Load customizable categories from localStorage or use defaults
  const getDefaultCategories = () => [
    { title: "Kurtis set", image: "/placeholder-women.jpg" },
    { title: "Cord Sets", image: "/placeholder-new.jpg" },
    { title: "Gowns", image: "/placeholder-men.jpg" },
    { title: "Sarees", image: "/placeholder-ethnic.jpg" },
    { title: "Kurtis", image: "/placeholder-western.jpg" },
    { title: "Duppatas", image: "/placeholder-wedding.jpg" },
  ];

  const [categoryCards, setCategoryCards] = useState(getDefaultCategories());

  useEffect(() => {
    // Load categories from localStorage if available
    const loadCategories = () => {
      const storedCategories = localStorage.getItem('landingCategories');
      console.log('Loading categories from localStorage:', storedCategories);
      
      if (storedCategories) {
        try {
          const categories = JSON.parse(storedCategories);
          console.log('Parsed categories:', categories);
          
          // Filter out any invalid categories and ensure proper structure
          const validCategories = categories.filter((cat: any) => 
            cat && cat.title && cat.image && cat.order
          );
          
          console.log('Valid categories:', validCategories);
          console.log('Setting categoryCards (all 6):', validCategories.slice(0, 6));
          
          setCategoryCards(validCategories.slice(0, 6)); // Show all 6 categories
        } catch (error) {
          console.error('Error loading categories:', error);
          console.error('Stored data was:', storedCategories);
        }
      } else {
        console.log('No stored categories found, using defaults');
      }
    };

    loadCategories();

    // Listen for storage changes (when admin saves from another tab)
    const handleStorageChange = (e: StorageEvent) => {
      console.log('Storage changed, key:', e.key, 'newValue:', e.newValue);
      if (e.key === 'landingCategories' && e.newValue) {
        console.log('Storage changed, reloading categories');
        loadCategories();
      }
    };

    // Listen for custom event (when admin saves from same tab)
    const handleCategoriesUpdate = (event: any) => {
      console.log('Categories update event received:', event.detail);
      loadCategories();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('categoriesUpdated', handleCategoriesUpdate);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('categoriesUpdated', handleCategoriesUpdate);
    };
  }, []);

  const navLinks = [
    { name: "New Arrivals", href: "#" },
    { name: "Categories", href: "#", hasDropdown: true },
    { name: "About", href: "#" },
  ];

  const categoriesList = [
    "Kurti Set",
    "Cord Sets", 
    "Gowns",
    "Sarees",
    "Kurtis",
    "Duppatas"
  ];

  const trustFeatures = [
    { icon: Truck, title: "Fast Shipping", description: "Free delivery on orders over $100" },
    { icon: Shield, title: "Premium Quality", description: "Handcrafted with finest materials" },
    { icon: Gift, title: "Custom Free Shipping", description: "Personalized packaging available" },
  ];

  return (
    <ParallaxProvider>
      <div className="min-h-screen bg-[#0E0E0E]">
        {/* Floating Navigation Elements */}
        <div className={`fixed top-0 left-0 right-0 z-50 p-4 sm:p-6 transition-transform duration-300 ease-in-out ${navVisible ? 'translate-y-0' : '-translate-y-full'}`}>
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            {/* Logo */}
            <div className="flex-shrink-0">
              <Image
                src="/logo.jpeg"
                alt="Aarya Clothings"
                width={180}
                height={75}
                className="h-12 sm:h-16 w-auto object-contain"
                priority
              />
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              {navLinks.map((link) => (
                <div key={link.name} className="relative">
                  {link.hasDropdown ? (
                    <div className="relative group">
                      <button
                        className="nav-link text-sm font-medium tracking-wide flex items-center gap-1"
                        onMouseEnter={() => setCategoriesDropdownOpen(true)}
                        onMouseLeave={() => setCategoriesDropdownOpen(false)}
                      >
                        {link.name}
                        <svg 
                          className={`w-4 h-4 transition-transform duration-200 ${categoriesDropdownOpen ? 'rotate-180' : ''}`}
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      
                      {/* Dropdown Menu */}
                      <div 
                        className={`absolute top-full left-0 mt-2 w-48 bg-[#1A1A1A] border border-[#D4AF37]/20 rounded-lg shadow-lg transition-all duration-200 z-50 ${
                          categoriesDropdownOpen ? 'opacity-100 visible translate-y-0' : 'opacity-0 invisible -translate-y-2'
                        }`}
                        onMouseEnter={() => setCategoriesDropdownOpen(true)}
                        onMouseLeave={() => setCategoriesDropdownOpen(false)}
                      >
                        <div className="py-2">
                          {categoriesList.map((category) => (
                            <a
                              key={category}
                              href="#"
                              className="block px-4 py-2 text-sm text-[#F4EDE4] hover:text-[#D4AF37] hover:bg-[#D4AF37]/10 transition-colors"
                            >
                              {category}
                            </a>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <a
                      href={link.href}
                      className="nav-link text-sm font-medium tracking-wide"
                    >
                      {link.name}
                    </a>
                  )}
                </div>
              ))}
            </nav>

            {/* Right Icons */}
            <div className="flex items-center space-x-4">
              <button className="p-2 text-[#F4EDE4] hover:text-[#D4AF37] transition-colors bg-[#0E0E0E]/50 backdrop-blur-sm rounded-lg">
                <Search className="w-5 h-5" />
              </button>
              {currentUser ? (
                <div className="relative group">
                  <button className="p-2 text-[#F4EDE4] hover:text-[#D4AF37] transition-colors bg-[#0E0E0E]/50 backdrop-blur-sm rounded-lg hidden sm:block">
                    <User className="w-5 h-5" />
                  </button>
                  <div className="absolute right-0 mt-2 w-48 bg-[#1A1A1A] border border-[#D4AF37]/20 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                    <div className="p-4">
                      <p className="text-sm font-medium text-[#F4EDE4] mb-1">{currentUser.name}</p>
                      <p className="text-xs text-[#B89C5A] mb-3">{currentUser.email}</p>
                      <div className="border-t border-[#D4AF37]/20 pt-3">
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-2 text-sm text-[#F4EDE4] hover:text-[#D4AF37] transition-colors"
                        >
                          <LogOut className="w-4 h-4" />
                          Logout
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <Link href="/login" className="p-2 text-[#F4EDE4] hover:text-[#D4AF37] transition-colors bg-[#0E0E0E]/50 backdrop-blur-sm rounded-lg hidden sm:block">
                  <User className="w-5 h-5" />
                </Link>
              )}
              <button className="p-2 text-[#F4EDE4] hover:text-[#D4AF37] transition-colors bg-[#0E0E0E]/50 backdrop-blur-sm rounded-lg">
                <ShoppingBag className="w-5 h-5" />
              </button>
              
              {/* Mobile Menu Button */}
              <button
                className="md:hidden p-2 text-[#F4EDE4] hover:text-[#D4AF37] transition-colors bg-[#0E0E0E]/50 backdrop-blur-sm rounded-lg"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden bg-[#1A1A1A] border border-[#D4AF37]/20 rounded-lg mt-4 mx-4 max-w-7xl">
              <div className="p-4 space-y-3">
                {navLinks.map((link) => (
                  <div key={link.name}>
                    {link.hasDropdown ? (
                      <div>
                        <button
                          onClick={() => setCategoriesDropdownOpen(!categoriesDropdownOpen)}
                          className="flex items-center justify-between w-full py-2 text-[#F4EDE4] hover:text-[#D4AF37] transition-colors border-b border-[#D4AF37]/10"
                        >
                          {link.name}
                          <svg 
                            className={`w-4 h-4 transition-transform duration-200 ${categoriesDropdownOpen ? 'rotate-180' : ''}`}
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        
                        {/* Mobile Dropdown */}
                        {categoriesDropdownOpen && (
                          <div className="pl-4 py-2 space-y-2">
                            {categoriesList.map((category) => (
                              <a
                                key={category}
                                href="#"
                                className="block py-1 text-sm text-[#F4EDE4]/80 hover:text-[#D4AF37] transition-colors"
                              >
                                {category}
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <a
                        href={link.href}
                        className="block py-2 text-[#F4EDE4] hover:text-[#D4AF37] transition-colors border-b border-[#D4AF37]/10"
                      >
                        {link.name}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Hero Section - Full Page with Parallax */}
        <section className="relative w-full h-screen flex items-center justify-center overflow-hidden parallax-section">
          {/* Parallax Background */}
          <div className="absolute inset-0 parallax-hero-bg parallax-slow">
            <div className="absolute inset-0 bg-[url('/hero-background.png')] bg-cover bg-center bg-fixed bg-no-repeat">
              <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/40 to-black/60"></div>
            </div>
          </div>
          
          {/* Floating Content */}
          <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 text-center parallax-content">
            <h2 className="text-4xl md:text-6xl lg:text-7xl font-semibold text-[#F4EDE4] mb-6 leading-tight animate-fade-in-up" style={{ fontFamily: 'var(--font-playfair)' }}>
              Elegance Redefined
            </h2>
            <p className="text-lg md:text-xl text-[#B89C5A] mb-8 subtitle-spacing tracking-wide animate-fade-in-up animation-delay-200">
              Discover the Essence of Royalty
            </p>
            <button className="btn-gold text-base md:text-lg animate-fade-in-up animation-delay-400">
              Shop Now
            </button>
          </div>
          
          {/* Scroll Indicator */}
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10 animate-bounce">
            <div className="w-6 h-10 border-2 border-[#D4AF37]/50 rounded-full flex justify-center">
              <div className="w-1 h-3 bg-[#D4AF37] rounded-full mt-2"></div>
            </div>
          </div>
          
          {/* Decorative gold accent */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent"></div>
        </section>

      {/* Category Strip */}
      <section className="relative py-16 md:py-24 scroll-animate">
        {/* Background Image */}
        <div className="absolute inset-0 bg-[url('/background.png')] bg-cover bg-center bg-fixed">
          <div className="absolute inset-0 bg-black/70"></div>
        </div>
        
        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
            {categoryCards.map((card, index) => (
              <div
                key={index}
                className="group relative aspect-[4/5] rounded-2xl overflow-hidden cursor-pointer scroll-animate bg-black/40 backdrop-blur-sm border border-[#D4AF37]/20"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {/* Overlay */}
                <div className="absolute inset-0 card-overlay"></div>
                
                {/* Text */}
                <div className="absolute bottom-0 left-0 right-0 p-6 text-center">
                  <h3 className="text-xl md:text-2xl font-semibold text-[#F4EDE4]" style={{ fontFamily: 'var(--font-playfair)' }}>
                    {card.title}
                  </h3>
                </div>
                
                {/* Hover border */}
                <div className="absolute inset-0 border-2 border-transparent group-hover:border-[#D4AF37]/50 rounded-2xl transition-colors duration-300"></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Customer Trust Strip */}
      <section className="py-12 md:py-16 bg-[#F6EFE7]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
            {trustFeatures.map((feature, index) => (
              <div key={index} className="flex flex-col items-center text-center">
                <div className="w-16 h-16 mb-4 rounded-full bg-[#0E0E0E] flex items-center justify-center">
                  <feature.icon className="w-7 h-7 text-[#D4AF37]" />
                </div>
                <h3 className="text-sm font-semibold text-[#0E0E0E] uppercase tracking-wider mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-[#1A1A1A]/60">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-[#D4AF37]/20">
        {/* Background Image */}
        <div className="absolute inset-0 bg-[url('/background.png')] bg-cover bg-center">
          <div className="absolute inset-0 bg-black/80"></div>
        </div>
        
        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
            {/* Brand Column */}
            <div className="col-span-2 md:col-span-1">
              <h3 className="text-xl font-semibold text-[#D4AF37] mb-4" style={{ fontFamily: 'var(--font-playfair)' }}>
                Aarya Clothings
              </h3>
              <p className="text-sm text-[#F4EDE4]/60 mb-4">
                Redefining elegance with premium ethnic and western wear for the modern royalty.
              </p>
            </div>
            
            {/* Links Columns */}
            <div>
              <h4 className="text-sm font-semibold text-[#D4AF37] uppercase tracking-wider mb-4">About Us</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Our Story</a></li>
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Careers</a></li>
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Press</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-[#D4AF37] uppercase tracking-wider mb-4">Customer Care</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Contact Us</a></li>
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Shipping</a></li>
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Returns</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-[#D4AF37] uppercase tracking-wider mb-4">Legal</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Terms & Conditions</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-[#D4AF37] uppercase tracking-wider mb-4">Follow Us</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Instagram</a></li>
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Facebook</a></li>
                <li><a href="#" className="text-sm text-[#F4EDE4]/60 hover:text-[#D4AF37] transition-colors">Pinterest</a></li>
              </ul>
            </div>
          </div>
          
          {/* Bottom Bar */}
          <div className="pt-8 border-t border-[#D4AF37]/20">
            <p className="text-center text-sm text-[#B89C5A]">
              © 2025 Aarya Clothings. All rights reserved. Crafted with elegance.
            </p>
          </div>
        </div>
      </footer>
      </div>
    </ParallaxProvider>
  );
}

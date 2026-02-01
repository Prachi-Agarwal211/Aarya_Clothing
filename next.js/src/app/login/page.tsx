"use client";

import { useState } from "react";
import { Eye, EyeOff, User, Lock, Mail, Info, MessageCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authenticateUser, TEST_CREDENTIALS } from "@/lib/credentials";

export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showPasswordTooltip, setShowPasswordTooltip] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpMethod, setOtpMethod] = useState('whatsapp'); // 'whatsapp' or 'email'
  const [isLogin, setIsLogin] = useState(true);
  const [showTestCredentials, setShowTestCredentials] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loginSuccess, setLoginSuccess] = useState('');
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoginSuccess('');

    // Get form data
    const formData = new FormData(e.target as HTMLFormElement);
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;

    // Authenticate user
    const result = authenticateUser(email, password);
    
    if (result.success && result.user) {
      setLoginSuccess(`Welcome back, ${result.user.name}! (${result.user.role})`);
      
      // Store user info in localStorage for persistence across pages
      localStorage.setItem('user', JSON.stringify(result.user));
      
      // Redirect based on role
      setTimeout(() => {
        if (result.user.role === 'admin') {
          router.push('/admin');
        } else {
          router.push('/');
        }
      }, 1500);
    } else {
      setLoginError(result.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-[#0E0E0E] flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-[#D4AF37]/10 rounded-full mb-4">
            <User className="w-10 h-10 text-[#D4AF37]" />
          </div>
          <h1 className="text-3xl font-semibold text-[#F4EDE4] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
            {isLogin ? 'Welcome Back' : 'Create Account'}
          </h1>
          <p className="text-[#B89C5A]">
            {isLogin ? 'Sign in to your account' : 'Join Aarya Clothings'}
          </p>
        </div>

        {/* Form */}
        <div className="bg-[#1A1A1A] rounded-2xl p-8 border border-[#D4AF37]/20">
          {/* Test Credentials Toggle */}
          <div className="mb-6 text-center">
            <button
              type="button"
              onClick={() => setShowTestCredentials(!showTestCredentials)}
              className="text-xs text-[#B89C5A] hover:text-[#D4AF37] underline"
            >
              {showTestCredentials ? 'Hide' : 'Show'} Test Credentials
            </button>
            
            {showTestCredentials && (
              <div className="mt-4 p-4 bg-[#0E0E0E] rounded-lg border border-[#D4AF37]/20">
                <p className="text-xs font-semibold text-[#D4AF37] mb-2">Test Credentials:</p>
                <div className="text-xs text-[#B89C5A] space-y-2">
                  <div>
                    <p className="font-semibold text-[#F4EDE4]">Admin:</p>
                    <p>Email: {TEST_CREDENTIALS.admin.email}</p>
                    <p>Password: {TEST_CREDENTIALS.admin.password}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-[#F4EDE4]">Customer:</p>
                    <p>Email: {TEST_CREDENTIALS.customers[0].email}</p>
                    <p>Password: {TEST_CREDENTIALS.customers[0].password}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Login Messages */}
          {loginError && (
            <div className="mb-4 p-3 bg-red-900/20 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400">{loginError}</p>
            </div>
          )}
          
          {loginSuccess && (
            <div className="mb-4 p-3 bg-green-900/20 border border-green-500/20 rounded-lg">
              <p className="text-sm text-green-400">{loginSuccess}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            {!isLogin && (
              <>
                {/* First Name and Last Name */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                      First Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                      <input
                        type="text"
                        className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                        placeholder="First name"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                      Last Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                      <input
                        type="text"
                        className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                        placeholder="Last name"
                      />
                    </div>
                  </div>
                </div>

                {/* Email Address */}
                <div>
                  <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                      type="email"
                      className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                      placeholder="Enter your email address"
                    />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    Password
                    <button
                      type="button"
                      onMouseEnter={() => setShowPasswordTooltip(true)}
                      onMouseLeave={() => setShowPasswordTooltip(false)}
                      className="ml-1 text-[#B89C5A] hover:text-[#D4AF37]"
                    >
                      <Info className="w-4 h-4" />
                    </button>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                      type={showPassword ? "text" : "password"}
                      className="w-full pl-10 pr-12 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                      placeholder="Create a strong password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#B89C5A] hover:text-[#D4AF37]"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  
                  {/* Password Requirements Tooltip */}
                  {showPasswordTooltip && (
                    <div className="absolute z-10 mt-2 p-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg shadow-lg">
                      <p className="text-xs text-[#F4EDE4] mb-2 font-semibold">Password must contain:</p>
                      <ul className="text-xs text-[#B89C5A] space-y-1">
                        <li>• Minimum 8 characters</li>
                        <li>• 1 uppercase letter (A-Z)</li>
                        <li>• 1 lowercase letter (a-z)</li>
                        <li>• 1 number (0-9)</li>
                        <li>• 1 special symbol (!@#$%^&*)</li>
                      </ul>
                    </div>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      className="w-full pl-10 pr-12 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                      placeholder="Confirm your password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#B89C5A] hover:text-[#D4AF37]"
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* OTP Verification */}
                <div>
                  <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    OTP Verification
                  </label>
                  
                  {/* OTP Method Selection */}
                  <div className="mb-4">
                    <p className="text-xs text-[#B89C5A] mb-2">Send OTP via:</p>
                    <div className="flex space-x-4">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="otpMethod"
                          value="whatsapp"
                          checked={otpMethod === 'whatsapp'}
                          onChange={(e) => setOtpMethod(e.target.value)}
                          className="w-4 h-4 text-[#D4AF37] bg-[#0E0E0E] border-[#D4AF37]/20 focus:ring-[#D4AF37]"
                        />
                        <span className="ml-2 text-sm text-[#F4EDE4]">WhatsApp</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="otpMethod"
                          value="email"
                          checked={otpMethod === 'email'}
                          onChange={(e) => setOtpMethod(e.target.value)}
                          className="w-4 h-4 text-[#D4AF37] bg-[#0E0E0E] border-[#D4AF37]/20 focus:ring-[#D4AF37]"
                        />
                        <span className="ml-2 text-sm text-[#F4EDE4]">Email</span>
                      </label>
                    </div>
                  </div>

                  {!otpSent ? (
                    <button
                      type="button"
                      onClick={() => setOtpSent(true)}
                      className="w-full py-3 bg-[#D4AF37] text-black rounded-lg font-medium hover:bg-[#C9A24D] transition-colors"
                    >
                      Send OTP to {otpMethod === 'whatsapp' ? 'WhatsApp' : 'Email Address'}
                    </button>
                  ) : (
                    <>
                      <div className="flex space-x-2 mb-3">
                        <input
                          type="text"
                          maxLength={1}
                          className="w-12 h-12 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] text-center focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                          placeholder="0"
                        />
                        <input
                          type="text"
                          maxLength={1}
                          className="w-12 h-12 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] text-center focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                          placeholder="0"
                        />
                        <input
                          type="text"
                          maxLength={1}
                          className="w-12 h-12 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] text-center focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                          placeholder="0"
                        />
                        <input
                          type="text"
                          maxLength={1}
                          className="w-12 h-12 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] text-center focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                          placeholder="0"
                        />
                      </div>
                      <p className="text-xs text-[#B89C5A] mb-3">
                        4-digit code sent to your {otpMethod}
                      </p>
                      <div className="flex items-center justify-between">
                        <button
                          type="button"
                          onClick={() => setOtpSent(false)}
                          className="text-sm text-[#D4AF37] hover:text-[#B89C5A]"
                        >
                          Change {otpMethod}
                        </button>
                        <button
                          type="button"
                          className="text-sm text-[#D4AF37] hover:text-[#B89C5A]"
                        >
                          Resend OTP
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </>
            )}

            {isLogin && (
              <>
                {/* Email/Phone for Login */}
                <div>
                  <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    Email Address or Phone Number
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                      type="text"
                      name="email"
                      className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                      placeholder="Enter your email or phone number"
                    />
                  </div>
                </div>

                {/* Password for Login */}
                <div>
                  <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      className="w-full pl-10 pr-12 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                      placeholder="Enter your password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#B89C5A] hover:text-[#D4AF37]"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="w-4 h-4 text-[#D4AF37] bg-[#0E0E0E] border-[#D4AF37]/20 rounded focus:ring-[#D4AF37]"
                    />
                    <span className="ml-2 text-sm text-[#F4EDE4]">Remember me</span>
                  </label>
                  <a href="#" className="text-sm text-[#D4AF37] hover:text-[#B89C5A]">
                    Forgot password?
                  </a>
                </div>
              </>
            )}

            <button
              type="submit"
              className="w-full btn-gold text-base font-medium"
            >
              {isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Switch between Login/Register */}
          <div className="mt-6 text-center">
            <p className="text-sm text-[#B89C5A]">
              {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-[#D4AF37] hover:text-[#B89C5A] font-medium"
              >
                {isLogin ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </div>
        </div>

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <Link 
            href="/"
            className="text-sm text-[#B89C5A] hover:text-[#D4AF37] transition-colors"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}

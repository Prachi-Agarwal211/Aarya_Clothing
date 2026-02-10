"use client";

import { useState, useEffect } from "react";
import { Eye, EyeOff, User, Lock, Mail, Info, MessageCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { sendOTP, verifyOTP, resendOTP } from "@/lib/auth";

export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showPasswordTooltip, setShowPasswordTooltip] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpMethod, setOtpMethod] = useState<'EMAIL' | 'WHATSAPP'>('EMAIL');
  const [otpCode, setOtpCode] = useState(['', '', '', '', '', '']);
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otpError, setOtpError] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loginError, setLoginError] = useState('');
  const [loginSuccess, setLoginSuccess] = useState('');
  const router = useRouter();

  const { login, register } = useAuth(); // Use auth hook
  const [loading, setLoading] = useState(false); // Add loading state

  // OTP Handlers
  const handleSendOTP = async (email: string) => {
    if (!email) {
      setOtpError('Email is required for OTP verification');
      return;
    }

    setOtpLoading(true);
    setOtpError('');

    try {
      const result = await sendOTP(email, 'email_verification', 'verify');
      if (result.success) {
        setOtpSent(true);
        setLoginSuccess(`OTP sent to ${email}`);
      } else {
        setOtpError(result.message || 'Failed to send OTP');
      }
    } catch (error: any) {
      setOtpError(error.message || 'Failed to send OTP');
    } finally {
      setOtpLoading(false);
    }
  };

  const handleVerifyOTP = async (email: string) => {
    const code = otpCode.join('');
    if (code.length !== 6) {
      setOtpError('Please enter the complete 6-digit code');
      return;
    }

    if (!email) {
      setOtpError('Email is required for OTP verification');
      return;
    }

    setOtpLoading(true);
    setOtpError('');

    try {
      const result = await verifyOTP(email, code, 'email_verification', 'verify');
      if (result.success && result.data?.verified) {
        setOtpVerified(true);
        setLoginSuccess('OTP verified successfully!');
        // Clear OTP inputs
        setOtpCode(['', '', '', '']);
      } else {
        setOtpError(result.message || 'Invalid OTP code');
      }
    } catch (error: any) {
      setOtpError(error.message || 'Failed to verify OTP');
    } finally {
      setOtpLoading(false);
    }
  };

  const handleResendOTP = async (email: string) => {
    if (!email) {
      setOtpError('Email is required for OTP verification');
      return;
    }

    setOtpLoading(true);
    setOtpError('');

    try {
      const result = await resendOTP(email, 'email_verification', 'verify');
      if (result.success) {
        setLoginSuccess(`New OTP sent to ${email}`);
        // Clear OTP inputs
        setOtpCode(['', '', '', '']);
      } else {
        setOtpError(result.message || 'Failed to resend OTP');
      }
    } catch (error: any) {
      setOtpError(error.message || 'Failed to resend OTP');
    } finally {
      setOtpLoading(false);
    }
  };

  const handleOTPInputChange = (index: number, value: string) => {
    if (value.length <= 1 && /^\d*$/.test(value)) {
      const newOtpCode = [...otpCode];
      newOtpCode[index] = value;
      setOtpCode(newOtpCode);

      // Auto-focus next input
      if (value && index < 5) {
        const nextInput = document.getElementById(`otp-input-${index + 1}`) as HTMLInputElement;
        if (nextInput) nextInput.focus();
      }
    }
  };

  const handleOTPKeyDown = (index: number, e: React.KeyboardEvent) => {
    // Handle backspace to go to previous input
    if (e.key === 'Backspace' && !otpCode[index] && index > 0) {
      const prevInput = document.getElementById(`otp-input-${index - 1}`) as HTMLInputElement;
      if (prevInput) prevInput.focus();
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoginSuccess('');
    setLoading(true); // Add loading state

    const formData = new FormData(e.target as HTMLFormElement);

    if (isLogin) {
      const username = formData.get('email') as string; // Login uses email as username
      const password = formData.get('password') as string;
      const rememberMe = (e.target as HTMLFormElement).querySelector<HTMLInputElement>('input[type="checkbox"]')?.checked || false;

      // Basic validation
      if (!username || !password) {
        setLoginError('Please enter both email/username and password.');
        setLoading(false);
        return;
      }

      // Enhanced validation for login identifier
      if (username.includes('@')) {
        // Email validation
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(username)) {
          setLoginError('Please enter a valid email address.');
          setLoading(false);
          return;
        }
      } else {
        // Username validation
        if (username.length < 3) {
          setLoginError('Username must be at least 3 characters long.');
          setLoading(false);
          return;
        }
        if (!/^[a-zA-Z0-9_]+$/.test(username)) {
          setLoginError('Username can only contain letters, numbers, and underscores.');
          setLoading(false);
          return;
        }
      }

      const result = await login(username, password, rememberMe);

      if (result.success) {
        setLoginSuccess('Login successful! Redirecting...');
      } else {
        setLoginError(result.message || 'Login failed. Please check your credentials.');
      }
    } else {
      // Registration Logic with OTP
      const email = formData.get('email') as string;
      const password = formData.get('password') as string;
      const username = formData.get('username') as string;
      const firstName = formData.get('firstName') as string;
      const lastName = formData.get('lastName') as string;
      const fullName = `${firstName} ${lastName}`.trim();

      // Basic client-side validation
      if (!username || !email || !password) {
        setLoginError('Please fill in all required fields.');
        setLoading(false);
        return;
      }

      if (!firstName || !lastName) {
        setLoginError('Please enter your first and last name.');
        setLoading(false);
        return;
      }

      if (username.length < 3) {
        setLoginError('Username must be at least 3 characters long.');
        setLoading(false);
        return;
      }

      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        setLoginError('Please enter a valid email address.');
        setLoading(false);
        return;
      }

      // Get confirm password value
      const confirmPassword = formData.get('confirmPassword') as string;

      if (password !== confirmPassword) {
        setLoginError('Passwords do not match.');
        setLoading(false);
        return;
      }

      // Password validation
      if (password.length < 8) {
        setLoginError('Password must be at least 8 characters long.');
        setLoading(false);
        return;
      }

      if (!/(?=.*[a-z])/.test(password)) {
        setLoginError('Password must contain at least one lowercase letter.');
        setLoading(false);
        return;
      }

      if (!/(?=.*[A-Z])/.test(password)) {
        setLoginError('Password must contain at least one uppercase letter.');
        setLoading(false);
        return;
      }

      if (!(/.*\d/.test(password))) {
        setLoginError('Password must contain at least one number.');
        setLoading(false);
        return;
      }

      // OTP verification is now optional for registration
      // Users can choose to verify email but it's not required
      if (otpMethod === 'email' && !otpVerified) {
        console.log('Proceeding without OTP verification (optional)');
        // OTP is optional for basic registration - can be enabled later
        // setLoginError('Please verify your email with OTP before registering.');
        // return;
      }

      const result = await register({
        email,
        username,
        password,
        full_name: fullName,
        role: 'customer'
      });

      if (result.success) {
        setLoginSuccess('Account created! Logging you in...');
        // Auto-login after successful registration
        setTimeout(async () => {
          const loginResult = await login(email, password, false);
          if (loginResult.success) {
            setLoginSuccess('Registration successful! Redirecting...');
          } else {
            setLoginError('Account created but auto-login failed. Please login manually.');
            setTimeout(() => setIsLogin(true), 2000);
          }
        }, 1500);
      } else {
        setLoginError(result.message || 'Registration failed. Please try again.');
      }
    }

    setLoading(false); // Reset loading state
  };

  // Effect to redirect when user is authenticated
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'admin') {
        router.push('/admin');
      } else if (user.role === 'staff') {
        router.push('/admin'); // or /staff
      } else {
        router.push('/');
      }
    }
  }, [isAuthenticated, user, router]);

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
                {/* Username (Required) */}
                <div>
                  <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    Username
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                      type="text"
                      name="username"
                      required
                      className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                      placeholder="Choose a username"
                    />
                  </div>
                </div>

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
                        name="firstName"
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
                        name="lastName"
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
                      name="email"
                      required
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
                      name="password"
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
                      name="confirmPassword"
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

                  setOtpVerified(false);
                  setOtpCode(['', '', '', '', '', '']);
                  setOtpError('');
                          }}
                  className="w-4 h-4 text-[#D4AF37] bg-[#0E0E0E] border-[#D4AF37]/20 focus:ring-[#D4AF37]"
                        />
                  <span className="ml-2 text-sm text-[#F4EDE4]">Email</span>
                </label>
              </div>
        </div>

        {!otpSent ? (
          <button
            type="button"
            onClick={() => {
              const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
              const email = emailInput?.value;
              handleSendOTP(email);
            }}
            disabled={otpLoading}
            className="w-full py-3 bg-[#D4AF37] text-black rounded-lg font-medium hover:bg-[#C9A24D] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {otpLoading ? 'Sending...' : 'Send OTP to Email Address'}
          </button>
        ) : (
          <>
            <div className="flex space-x-2 mb-3">
              {otpCode.map((digit, index) => (
                <input
                  key={index}
                  id={`otp-input-${index}`}
                  type="text"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOTPInputChange(index, e.target.value)}
                  onKeyDown={(e) => handleOTPKeyDown(index, e)}
                  className="w-10 h-10 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] text-center focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                  placeholder="0"
                />
              ))}
            </div>

            {otpError && (
              <div className="mb-3 p-2 bg-red-900/20 border border-red-500/20 rounded-lg">
                <p className="text-xs text-red-400">{otpError}</p>
              </div>
            )}

            <p className="text-xs text-[#B89C5A] mb-3">
              {otpVerified ? '✓ Email verified successfully!' : '6-digit code sent to your email'}
            </p>

            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => {
                  setOtpSent(false);
                  setOtpVerified(false);
                  setOtpCode(['', '', '', '', '', '']);
                  setOtpError('');
                }}
                className="text-sm text-[#D4AF37] hover:text-[#B89C5A]"
              >
                Change Email
              </button>
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
                    const email = emailInput?.value;
                    handleResendOTP(email);
                  }}
                  disabled={otpLoading}
                  className="text-sm text-[#D4AF37] hover:text-[#B89C5A] disabled:opacity-50"
                >
                  {otpLoading ? 'Sending...' : 'Resend OTP'}
                </button>
                {!otpVerified && (
                  <button
                    type="button"
                    onClick={() => {
                      const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
                      const email = emailInput?.value;
                      handleVerifyOTP(email);
                    }}
                    disabled={otpLoading}
                    className="text-sm bg-[#D4AF37] text-black px-3 py-1 rounded font-medium hover:bg-[#C9A24D] disabled:opacity-50"
                  >
                    {otpLoading ? 'Verifying...' : 'Verify'}
                  </button>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}

{
  isLogin && (
    <>
      {/* Email/Username for Login */}
      <div>
        <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
          Email Address or Username
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
          <input
            type="text"
            name="email"
            className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
            placeholder="Enter your email or username"
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
        <Link href="/forgot-password" className="text-sm text-[#D4AF37] hover:text-[#B89C5A]">
          Forgot password?
        </Link>
      </div>
    </>
  )
}

<button
  type="submit"
  className="w-full btn-gold text-base font-medium"
  disabled={loading}
>
  {loading ? (isLogin ? 'Signing In...' : 'Creating Account...') : (isLogin ? 'Sign In' : 'Create Account')}
</button>
          </form >

  {/* Switch between Login/Register */ }
  < div className = "mt-6 text-center" >
    <p className="text-sm text-[#B89C5A]">
      {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
      <button
        onClick={() => setIsLogin(!isLogin)}
        className="text-[#D4AF37] hover:text-[#B89C5A] font-medium"
      >
        {isLogin ? 'Sign Up' : 'Sign In'}
      </button>
    </p>
          </div >
        </div >

  {/* Back to Home */ }
  < div className = "mt-6 text-center" >
    <Link
      href="/"
      className="text-sm text-[#B89C5A] hover:text-[#D4AF37] transition-colors"
    >
      ← Back to Home
    </Link>
        </div >
      </div >
    </div >
  );
}

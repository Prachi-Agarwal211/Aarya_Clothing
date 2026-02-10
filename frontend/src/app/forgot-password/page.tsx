"use client";

import { useState } from "react";
import { Mail, MessageCircle, ArrowLeft, CheckCircle } from "lucide-react";
import Link from "next/link";
import { api, getErrorMessage } from "@/lib/api";

type Step = "request" | "verify" | "reset" | "success";
type OTPMethod = "EMAIL" | "WHATSAPP";

export default function ForgotPassword() {
    const [step, setStep] = useState<Step>("request");
    const [otpMethod, setOtpMethod] = useState<OTPMethod>("EMAIL");
    const [identifier, setIdentifier] = useState(""); // Email or phone
    const [otp, setOtp] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [expiresIn, setExpiresIn] = useState(600); // 10 minutes default

    const handleRequestOTP = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setErrorMessage("");

        try {
            const response = await api.post("/api/v1/auth/forgot-password-otp", null, {
                params: {
                    identifier,
                    otp_type: otpMethod
                }
            });

            setExpiresIn(response.data.expires_in || 600);
            setStep("verify");
        } catch (error: any) {
            setErrorMessage(getErrorMessage(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (newPassword !== confirmPassword) {
            setErrorMessage("Passwords do not match");
            return;
        }

        if (newPassword.length < 8) {
            setErrorMessage("Password must be at least 8 characters");
            return;
        }

        setIsLoading(true);
        setErrorMessage("");

        try {
            await api.post("/api/v1/auth/reset-password-otp", null, {
                params: {
                    identifier,
                    otp_code: otp,
                    new_password: newPassword,
                    otp_type: otpMethod
                }
            });

            setStep("success");
        } catch (error: any) {
            setErrorMessage(getErrorMessage(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleResendOTP = async () => {
        setIsLoading(true);
        setErrorMessage("");

        try {
            const response = await api.post("/api/v1/auth/forgot-password-otp", null, {
                params: {
                    identifier,
                    otp_type: otpMethod
                }
            });

            setExpiresIn(response.data.expires_in || 600);
            setErrorMessage("");
        } catch (error: any) {
            setErrorMessage(getErrorMessage(error));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#0E0E0E] flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-semibold text-[#F4EDE4] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
                        Reset Password
                    </h1>
                    <p className="text-[#B89C5A]">
                        {step === "request" && "Enter your details to receive an OTP"}
                        {step === "verify" && "Enter the verification code we sent"}
                        {step === "reset" && "Create a new password"}
                        {step === "success" && "Password reset successful!"}
                    </p>
                </div>

                {/* Content */}
                <div className="bg-[#1A1A1A] rounded-2xl p-8 border border-[#D4AF37]/20">
                    {/* Success Step */}
                    {step === "success" && (
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-900/20 rounded-full mb-4">
                                <CheckCircle className="w-8 h-8 text-green-500" />
                            </div>
                            <h3 className="text-xl text-[#F4EDE4] font-medium mb-2">Password Changed!</h3>
                            <p className="text-[#B89C5A] mb-6">
                                Your password has been reset successfully. You can now log in with your new password.
                            </p>
                            <Link
                                href="/login"
                                className="inline-block w-full py-3 bg-[#D4AF37] text-black rounded-lg font-medium hover:bg-[#C9A24D] transition-colors"
                            >
                                Go to Login
                            </Link>
                        </div>
                    )}

                    {/* Request OTP Step */}
                    {step === "request" && (
                        <form onSubmit={handleRequestOTP} className="space-y-6">
                            {errorMessage && (
                                <div className="p-3 bg-red-900/20 border border-red-500/20 rounded-lg">
                                    <p className="text-sm text-red-400">{errorMessage}</p>
                                </div>
                            )}

                            {/* OTP Method Selection */}
                            <div>
                                <label className="block text-sm font-medium text-[#F4EDE4] mb-3">
                                    Verification Method
                                </label>
                                <div className="flex gap-4">
                                    <button
                                        type="button"
                                        onClick={() => setOtpMethod("EMAIL")}
                                        className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                                            otpMethod === "EMAIL"
                                                ? "border-[#D4AF37] bg-[#D4AF37]/10"
                                                : "border-[#D4AF37]/20 bg-[#0E0E0E]"
                                        }`}
                                    >
                                        <Mail className="w-6 h-6 text-[#D4AF37] mx-auto mb-2" />
                                        <span className="text-sm text-[#F4EDE4] block">Email</span>
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setOtpMethod("WHATSAPP")}
                                        className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                                            otpMethod === "WHATSAPP"
                                                ? "border-[#D4AF37] bg-[#D4AF37]/10"
                                                : "border-[#D4AF37]/20 bg-[#0E0E0E]"
                                        }`}
                                    >
                                        <MessageCircle className="w-6 h-6 text-[#D4AF37] mx-auto mb-2" />
                                        <span className="text-sm text-[#F4EDE4] block">WhatsApp</span>
                                    </button>
                                </div>
                            </div>

                            {/* Email or Phone Input */}
                            <div>
                                <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                                    {otpMethod === "EMAIL" ? "Email Address" : "Phone Number"}
                                </label>
                                <div className="relative">
                                    {otpMethod === "EMAIL" ? (
                                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                                    ) : (
                                        <MessageCircle className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                                    )}
                                    <input
                                        type={otpMethod === "EMAIL" ? "email" : "tel"}
                                        required
                                        value={identifier}
                                        onChange={(e) => setIdentifier(e.target.value)}
                                        className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                                        placeholder={otpMethod === "EMAIL" ? "Enter your email" : "Enter phone (+1234567890)"}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full btn-gold text-base font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? "Sending..." : "Send OTP"}
                            </button>
                        </form>
                    )}

                    {/* Verify OTP & Reset Password Step */}
                    {step === "verify" && (
                        <form onSubmit={handleResetPassword} className="space-y-6">
                            {errorMessage && (
                                <div className="p-3 bg-red-900/20 border border-red-500/20 rounded-lg">
                                    <p className="text-sm text-red-400">{errorMessage}</p>
                                </div>
                            )}

                            {/* OTP Input */}
                            <div>
                                <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                                    Verification Code
                                </label>
                                <input
                                    type="text"
                                    required
                                    maxLength={6}
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                                    className="w-full px-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] text-center text-2xl tracking-widest focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                                    placeholder="000000"
                                />
                                <p className="mt-2 text-xs text-[#B89C5A] text-center">
                                    Sent to {identifier} via {otpMethod === "EMAIL" ? "email" : "WhatsApp"}
                                </p>
                            </div>

                            {/* New Password */}
                            <div>
                                <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                                    New Password
                                </label>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    required
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                                    placeholder="Enter new password"
                                    minLength={8}
                                />
                            </div>

                            {/* Confirm Password */}
                            <div>
                                <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                                    Confirm Password
                                </label>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    required
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                                    placeholder="Confirm new password"
                                    minLength={8}
                                />
                            </div>

                            {/* Show Password Toggle */}
                            <label className="flex items-center text-sm text-[#B89C5A] cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={showPassword}
                                    onChange={(e) => setShowPassword(e.target.checked)}
                                    className="mr-2"
                                />
                                Show password
                            </label>

                            <button
                                type="submit"
                                disabled={isLoading || otp.length !== 6}
                                className="w-full btn-gold text-base font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? "Resetting..." : "Reset Password"}
                            </button>

                            {/* Resend OTP */}
                            <div className="text-center">
                                <button
                                    type="button"
                                    onClick={handleResendOTP}
                                    disabled={isLoading}
                                    className="text-sm text-[#D4AF37] hover:underline disabled:opacity-50"
                                >
                                    Didn't receive code? Resend
                                </button>
                            </div>
                        </form>
                    )}
                </div>

                {/* Back Link */}
                {step !== "success" && (
                    <div className="mt-6 text-center">
                        <Link
                            href="/login"
                            className="inline-flex items-center text-sm text-[#B89C5A] hover:text-[#D4AF37] transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4 mr-1" />
                            Back to Login
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}

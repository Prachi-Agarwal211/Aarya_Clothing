"use client";

import { useState } from "react";
import { Mail, ArrowLeft, CheckCircle } from "lucide-react";
import Link from "next/link";
import { api, getErrorMessage } from "@/lib/api";

export default function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setErrorMessage("");
        setSuccessMessage("");

        try {
            // Backend endpoint: /api/v1/auth/forgot-password
            await api.post("/api/v1/auth/forgot-password", { email });
            setSuccessMessage("If an account exists with this email, you will receive a password reset link.");
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
                        Enter your email to receive reset instructions
                    </p>
                </div>

                {/* Content */}
                <div className="bg-[#1A1A1A] rounded-2xl p-8 border border-[#D4AF37]/20">
                    {successMessage ? (
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-900/20 rounded-full mb-4">
                                <CheckCircle className="w-8 h-8 text-green-500" />
                            </div>
                            <h3 className="text-xl text-[#F4EDE4] font-medium mb-2">Check your email</h3>
                            <p className="text-[#B89C5A] mb-6">
                                {successMessage}
                            </p>
                            <Link
                                href="/login"
                                className="inline-block w-full py-3 bg-[#D4AF37] text-black rounded-lg font-medium hover:bg-[#C9A24D] transition-colors"
                            >
                                Back to Login
                            </Link>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-6">
                            {errorMessage && (
                                <div className="p-3 bg-red-900/20 border border-red-500/20 rounded-lg">
                                    <p className="text-sm text-red-400">{errorMessage}</p>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                                    Email Address
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                                    <input
                                        type="email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full pl-10 pr-4 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                                        placeholder="Enter your email address"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full btn-gold text-base font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? "Sending..." : "Send Reset Link"}
                            </button>
                        </form>
                    )}
                </div>

                {/* Back Link */}
                <div className="mt-6 text-center">
                    <Link
                        href="/login"
                        className="inline-flex items-center text-sm text-[#B89C5A] hover:text-[#D4AF37] transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4 mr-1" />
                        Back to Login
                    </Link>
                </div>
            </div>
        </div>
    );
}

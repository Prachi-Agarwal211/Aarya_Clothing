"use client";

import { useState, useEffect, Suspense } from "react";
import { Lock, Eye, EyeOff, CheckCircle, AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api, getErrorMessage } from "@/lib/api";

function ResetPasswordForm() {
    const searchParams = useSearchParams();
    const token = searchParams.get("token");
    const router = useRouter();

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [status, setStatus] = useState<'verifying' | 'valid' | 'invalid' | 'success'>('verifying');
    const [errorMessage, setErrorMessage] = useState("");

    // Verify token on mount
    useEffect(() => {
        if (!token) {
            setStatus('invalid');
            setErrorMessage("Missing reset token.");
            return;
        }

        const verifyToken = async () => {
            try {
                await api.get(`/api/v1/auth/verify-reset-token/${token}`);
                setStatus('valid');
            } catch (error) {
                setStatus('invalid');
                setErrorMessage("Invalid or expired password reset token.");
            }
        };

        verifyToken();
    }, [token]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            setErrorMessage("Passwords do not match");
            return;
        }

        setIsLoading(true);
        setErrorMessage("");

        try {
            await api.post("/api/v1/auth/reset-password", {
                token,
                new_password: password
            });
            setStatus('success');
        } catch (error) {
            setErrorMessage(getErrorMessage(error));
        } finally {
            setIsLoading(false);
        }
    };

    if (status === 'verifying') {
        return (
            <div className="text-center text-[#B89C5A]">
                Verifying link...
            </div>
        );
    }

    if (status === 'invalid') {
        return (
            <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-red-900/20 rounded-full mb-4">
                    <AlertCircle className="w-8 h-8 text-red-500" />
                </div>
                <h3 className="text-xl text-[#F4EDE4] font-medium mb-2">Invalid Link</h3>
                <p className="text-[#B89C5A] mb-6">
                    {errorMessage}
                </p>
                <Link
                    href="/forgot-password"
                    className="inline-block w-full py-3 bg-[#D4AF37] text-black rounded-lg font-medium hover:bg-[#C9A24D] transition-colors"
                >
                    Request New Link
                </Link>
            </div>
        );
    }

    if (status === 'success') {
        return (
            <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-900/20 rounded-full mb-4">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
                <h3 className="text-xl text-[#F4EDE4] font-medium mb-2">Password Reset!</h3>
                <p className="text-[#B89C5A] mb-6">
                    Your password has been successfully reset.
                </p>
                <Link
                    href="/login"
                    className="inline-block w-full py-3 bg-[#D4AF37] text-black rounded-lg font-medium hover:bg-[#C9A24D] transition-colors"
                >
                    Sign In Now
                </Link>
            </div>
        );
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {errorMessage && (
                <div className="p-3 bg-red-900/20 border border-red-500/20 rounded-lg">
                    <p className="text-sm text-red-400">{errorMessage}</p>
                </div>
            )}

            <div>
                <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    New Password
                </label>
                <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                        type={showPassword ? "text" : "password"}
                        required
                        minLength={8}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full pl-10 pr-12 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                        placeholder="Min 8 chars"
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

            <div>
                <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                    Confirm Password
                </label>
                <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#B89C5A]" />
                    <input
                        type={showPassword ? "text" : "password"}
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full pl-10 pr-12 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg text-[#F4EDE4] placeholder-[#B89C5A] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]"
                        placeholder="Confirm password"
                    />
                </div>
            </div>

            <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-gold text-base font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {isLoading ? "Resetting..." : "Reset Password"}
            </button>
        </form>
    );
}

export default function ResetPassword() {
    return (
        <div className="min-h-screen bg-[#0E0E0E] flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-semibold text-[#F4EDE4] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
                        Set New Password
                    </h1>
                </div>

                <div className="bg-[#1A1A1A] rounded-2xl p-8 border border-[#D4AF37]/20">
                    <Suspense fallback={<div className="text-[#B89C5A] text-center">Loading...</div>}>
                        <ResetPasswordForm />
                    </Suspense>
                </div>
            </div>
        </div>
    );
}

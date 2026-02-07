"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { User, LogOut, Package, MapPin, Settings } from "lucide-react";
import Link from "next/link";

export default function ProfilePage() {
    const { user, logout, isAuthenticated, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push("/login");
        }
    }, [loading, isAuthenticated, router]);

    if (loading) {
        return <div className="min-h-screen bg-[#0E0E0E] flex items-center justify-center text-[#B89C5A]">Loading...</div>;
    }

    if (!user) return null;

    return (
        <div className="min-h-screen bg-[#0E0E0E] pt-24 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <h1 className="text-3xl font-semibold text-[#F4EDE4]" style={{ fontFamily: 'var(--font-playfair)' }}>
                        My Account
                    </h1>
                    <button
                        onClick={() => logout()}
                        className="flex items-center gap-2 px-4 py-2 border border-[#D4AF37]/30 rounded-lg text-[#B89C5A] hover:bg-[#D4AF37]/10 transition-colors"
                    >
                        <LogOut className="w-4 h-4" />
                        <span>Sign Out</span>
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* User Info Card */}
                    <div className="bg-[#1A1A1A] p-6 rounded-xl border border-[#D4AF37]/10">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-16 h-16 bg-[#D4AF37]/10 rounded-full flex items-center justify-center text-[#D4AF37]">
                                <User className="w-8 h-8" />
                            </div>
                            <div>
                                <h2 className="text-xl font-medium text-[#F4EDE4]">{user.full_name}</h2>
                                <p className="text-[#B89C5A] text-sm">{user.email}</p>
                                <div className="mt-1 inline-block px-2 py-0.5 bg-[#D4AF37]/20 rounded text-xs text-[#D4AF37] capitalize">
                                    {user.role}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="p-3 bg-[#0E0E0E] rounded-lg border border-[#D4AF37]/5">
                                <p className="text-xs text-[#666]">Username</p>
                                <p className="text-[#EAEAEA]">{user.username}</p>
                            </div>
                            <div className="p-3 bg-[#0E0E0E] rounded-lg border border-[#D4AF37]/5">
                                <p className="text-xs text-[#666]">Phone</p>
                                <p className="text-[#EAEAEA]">{user.phone || 'Not verified'}</p>
                            </div>
                        </div>
                    </div>

                    {/* Quick Actions / Dashboard */}
                    <div className="md:col-span-2 space-y-6">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <Link href="/orders" className="bg-[#1A1A1A] p-6 rounded-xl border border-[#D4AF37]/10 hover:border-[#D4AF37]/30 transition-all group">
                                <Package className="w-8 h-8 text-[#B89C5A] group-hover:text-[#D4AF37] mb-4" />
                                <h3 className="text-lg font-medium text-[#F4EDE4] mb-1">My Orders</h3>
                                <p className="text-sm text-[#666]">View and track your orders</p>
                            </Link>

                            <Link href="/addresses" className="bg-[#1A1A1A] p-6 rounded-xl border border-[#D4AF37]/10 hover:border-[#D4AF37]/30 transition-all group">
                                <MapPin className="w-8 h-8 text-[#B89C5A] group-hover:text-[#D4AF37] mb-4" />
                                <h3 className="text-lg font-medium text-[#F4EDE4] mb-1">Addresses</h3>
                                <p className="text-sm text-[#666]">Manage delivery addresses</p>
                            </Link>

                            {user.role === 'admin' && (
                                <Link href="/admin" className="bg-[#1A1A1A] p-6 rounded-xl border border-[#D4AF37]/10 hover:border-[#D4AF37]/30 transition-all group sm:col-span-2">
                                    <Settings className="w-8 h-8 text-[#B89C5A] group-hover:text-[#D4AF37] mb-4" />
                                    <h3 className="text-lg font-medium text-[#F4EDE4] mb-1">Admin Dashboard</h3>
                                    <p className="text-sm text-[#666]">Access administrative controls</p>
                                </Link>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

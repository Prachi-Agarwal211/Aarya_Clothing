import { api, getErrorMessage } from './api';

export enum UserRole {
    ADMIN = 'admin',
    STAFF = 'staff',
    CUSTOMER = 'customer',
}

export interface User {
    id: number;
    email: string;
    username: string;
    full_name: string;
    role: UserRole;
    is_active: boolean;
    email_verified: boolean;
    phone?: string;
    phone_verified?: boolean;
    created_at: string;
    last_login?: string;
}

export const checkAuth = async (): Promise<User | null> => {
    try {
        const response = await api.get<User>('/api/v1/users/me');
        return response.data;
    } catch (error) {
        return null;
    }
};

export const hasRole = (user: User | null, roles: UserRole[]): boolean => {
    if (!user) return false;
    return roles.includes(user.role);
};

export const isAdmin = (user: User | null): boolean => {
    return user?.role === UserRole.ADMIN;
};

export const isStaffOrAdmin = (user: User | null): boolean => {
    return !!user && (user.role === UserRole.ADMIN || user.role === UserRole.STAFF);
};

// OTP Functions
export interface OTPSendResponse {
    success: boolean;
    message: string;
    expires_in: number;
    email?: string;
    phone?: string;
}

export interface OTPVerifyResponse {
    success: boolean;
    message: string;
    verified: boolean;
}

export const sendOTP = async (email: string, otpType: string = 'email_verification', purpose: string = 'verify'): Promise<{ success: boolean; message?: string; data?: OTPSendResponse }> => {
    try {
        const response = await api.post<OTPSendResponse>('/api/v1/auth/send-otp', {
            email,
            otp_type: otpType,
            purpose
        });
        return { success: true, data: response.data };
    } catch (err: any) {
        const message = getErrorMessage(err);
        return { success: false, message };
    }
};

export const verifyOTP = async (email: string, otpCode: string, otpType: string = 'email_verification', purpose: string = 'verify'): Promise<{ success: boolean; message?: string; data?: OTPVerifyResponse }> => {
    try {
        const response = await api.post<OTPVerifyResponse>('/api/v1/auth/verify-otp', {
            email,
            otp_code: otpCode,
            otp_type: otpType,
            purpose
        });
        return { success: true, data: response.data };
    } catch (err: any) {
        const message = getErrorMessage(err);
        return { success: false, message };
    }
};

export const resendOTP = async (email: string, otpType: string = 'email_verification', purpose: string = 'verify'): Promise<{ success: boolean; message?: string; data?: OTPSendResponse }> => {
    try {
        const response = await api.post<OTPSendResponse>('/api/v1/auth/resend-otp', {
            email,
            otp_type: otpType,
            purpose
        });
        return { success: true, data: response.data };
    } catch (err: any) {
        const message = getErrorMessage(err);
        return { success: false, message };
    }
};

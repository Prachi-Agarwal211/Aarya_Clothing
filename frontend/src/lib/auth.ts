import { api } from './api';

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

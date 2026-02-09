/* eslint-disable deprecation/deprecation */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

// NOTE: middleware.ts is deprecated in favor of proxy.ts in Next.js 16+
// This is kept for compatibility and can be migrated later

// Define protected routes
const PROTECTED_ROUTES = ['/admin', '/staff', '/profile', '/checkout'];
const AUTH_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password'];

export async function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Check if accessing protected route
    const isProtectedRoute = PROTECTED_ROUTES.some(route => pathname.startsWith(route));
    const isAuthRoute = AUTH_ROUTES.some(route => pathname.startsWith(route));

    // Get token from cookies
    const token = request.cookies.get('access_token')?.value;

    // 1. Redirect unauthenticated users from protected routes
    if (isProtectedRoute && !token) {
        const url = new URL('/login', request.url);
        url.searchParams.set('from', pathname);
        return NextResponse.redirect(url);
    }

    // 2. Redirect authenticated users away from auth routes (login/register)
    if (isAuthRoute && token) {
        // Optional: Check role to decide where to go (admin vs home)
        // We can decode to token here if needed, but for now just sending to home/admin
        // Let's decode to be smarter
        try {
            const secret = new TextEncoder().encode(process.env.JWT_SECRET_KEY || 'your-secret-key-should-be-env-var');
            // Note: We might not have to secret here if it's not exposed to Edge env.
            // Usually JWT secret is server-side only. 
            // If we can't verify signature, we can at least decode payload unsafely for routing hints
            // OR we just redirect to a dashboard which then redirects if needed.

            // For now, redirect to home. User experience: if they go to /login while logged in, go to /
            return NextResponse.redirect(new URL('/', request.url));
        } catch (e) {
            // If token is invalid (expired/bad), let them stay on login page (and maybe clear cookie?)
            // We'll let to client-side handle invalid tokens via API calls
        }
    }

    // 3. Admin/Staff role protection
    if (pathname.startsWith('/admin') && token) {
        // Here we SHOULD verify role.
        // If we can't verify signature (no secret), we can just let it pass to the page
        // and let to page fetch /api/v1/users/me to verify role and redirect if needed.
        // This is safer than relying on an unverified token claim.
    }

    return NextResponse.next();
}

// eslint-disable-next-line deprecation/deprecation
export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * - public files (images, etc)
         */
        '/((?!api|_next/static|_next/image|favicon.ico).*)',
    ],
};

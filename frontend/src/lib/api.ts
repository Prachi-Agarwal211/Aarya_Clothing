import axios, { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import Cookies from 'js-cookie';

// API Configuration
const CORE_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const COMMERCE_API_URL = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL.replace('/api', '')}/commerce` : 'http://localhost:8010';
const PAYMENT_API_URL = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL.replace('/api', '')}/payment` : 'http://localhost:8020';

// Create Axios instance with default config
export const api: AxiosInstance = axios.create({
  baseURL: CORE_API_URL,
  withCredentials: true, // Important for HttpOnly cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export const commerceApi: AxiosInstance = axios.create({
  baseURL: COMMERCE_API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const paymentApi: AxiosInstance = axios.create({
  baseURL: PAYMENT_API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add Authorization header from cookie
// This is needed because commerce/payment services expect Bearer token
const addAuthHeader = (config: InternalAxiosRequestConfig) => {
  const token = Cookies.get('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

commerceApi.interceptors.request.use(addAuthHeader);
paymentApi.interceptors.request.use(addAuthHeader);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      // Check if it's a token expiration and we haven't retried yet
      // Note: Backend handles refresh via cookie on /refresh endpoint
      // To implement silent refresh, we would need to call refresh endpoint here
      // limiting retries to avoid infinite loops
      
      // For now, allow 401 to propagate so AuthContext can handle logout/redirect
    }

    // Standardize error message
    const errorMessage = 
      (error.response?.data as any)?.detail || 
      (error.response?.data as any)?.message || 
      error.message || 
      'An unexpected error occurred';
      
    // Attach formatted message to error object
    (error as any).formattedMessage = errorMessage;

    return Promise.reject(error);
  }
);

// Helper to get formatted error message
export const getErrorMessage = (error: any): string => {
  if (axios.isAxiosError(error)) {
    return (error as any).formattedMessage || error.message;
  }
  return error instanceof Error ? error.message : 'An unknown error occurred';
};

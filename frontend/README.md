# Aarya Clothing Frontend

Modern e-commerce frontend for Aarya Clothing women's wear brand, built with Next.js 16, TypeScript, and Tailwind CSS.

## 🛍️ Overview

This frontend application provides a complete shopping experience for the Aarya Clothing e-commerce platform, featuring:

- **Product Catalog** - Browse and search products with advanced filtering
- **Shopping Cart** - Real-time cart management with persistent storage
- **User Authentication** - Secure login, registration, and profile management
- **Order Management** - Complete order history and tracking
- **Payment Integration** - Seamless checkout with Razorpay and Stripe
- **Responsive Design** - Mobile-first design with Tailwind CSS

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** (Node.js 25.6.0+ recommended)
- **npm** or **yarn** package manager

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install

# Copy environment file
cp .env.example .env.local

# Start development server
npm run dev
# or
yarn dev
```

### Access Points
- **Development Server**: http://localhost:3000
- **API Documentation**: Available through backend services

## 🏗️ Technology Stack

### Core Framework
- **Next.js 16.1.6** - React framework with App Router
- **React 19.2.3** - UI library
- **TypeScript** - Type-safe development

### Styling & UI
- **Tailwind CSS 3.4.0** - Utility-first CSS framework
- **Lucide React 0.563.0** - Modern icon library
- **PostCSS** - CSS processing
- **Autoprefixer** - CSS compatibility

### State Management & Data
- **Axios 1.13.4** - HTTP client for API calls
- **js-cookie 3.0.5** - Cookie management for authentication
- **UUID 9.0.1** - Unique identifier generation

### Authentication & Security
- **Jose 6.1.3** - JWT token handling and validation
- **HTTP-only cookies** - Secure session management

### Cloud Integration
- **AWS SDK 3.980.0** - S3 integration for product images and assets
- **Cloudflare R2** - Alternative object storage support

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx         # Root layout component
│   │   ├── page.tsx           # Homepage
│   │   ├── products/          # Product pages
│   │   ├── cart/              # Shopping cart
│   │   ├── orders/            # Order management
│   │   ├── auth/              # Authentication pages
│   │   └── profile/           # User profile
│   ├── components/            # Reusable UI components
│   │   ├── ui/                # Base UI components
│   │   ├── product/           # Product-related components
│   │   ├── cart/              # Cart components
│   │   └── auth/              # Authentication components
│   ├── lib/                   # Utility libraries
│   │   ├── api.ts             # API client configuration
│   │   ├── auth.ts            # Authentication utilities
│   │   ├── utils.ts           # General utilities
│   │   └── constants.ts       # Application constants
│   ├── hooks/                 # Custom React hooks
│   │   ├── useAuth.ts         # Authentication hook
│   │   ├── useCart.ts         # Cart management hook
│   │   └── useApi.ts          # API request hook
│   ├── types/                 # TypeScript type definitions
│   │   ├── api.ts             # API response types
│   │   ├── product.ts         # Product types
│   │   └── user.ts            # User types
│   └── styles/                # Global styles
│       └── globals.css        # Global CSS with Tailwind
├── public/                    # Static assets
│   ├── images/                # Image assets
│   └── icons/                 # Icon files
├── package.json               # Dependencies and scripts
├── tsconfig.json              # TypeScript configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── next.config.js             # Next.js configuration
└── Dockerfile                 # Docker container configuration
```

## 🔧 Configuration

### Environment Variables

Create `.env.local` in the frontend root:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_COMMERCE_URL=http://localhost:8010
NEXT_PUBLIC_PAYMENT_URL=http://localhost:8020

# Application
NEXT_PUBLIC_APP_NAME="Aarya Clothing"
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Cloud Storage (AWS S3)
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_S3_BUCKET=aarya-clothing-assets

# Cloudflare R2 (Alternative)
NEXT_PUBLIC_R2_ACCOUNT_ID=your_account_id
NEXT_PUBLIC_R2_BUCKET_NAME=your_bucket_name

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_CHAT_SUPPORT=false
```

## 🚀 Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint

# Testing (when implemented)
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Run tests with coverage
```

## 🔗 API Integration

### Authentication Service (Port 8001)
- User registration and login
- JWT token management
- Password reset and OTP verification

### Commerce Service (Port 8010)
- Product catalog and search
- Shopping cart management
- Order processing and history

### Payment Service (Port 8020)
- Razorpay payment integration
- Stripe payment processing
- Payment status and refunds

## 🎨 UI Components

### Base Components
- **Button** - Consistent button styling with variants
- **Input** - Form inputs with validation
- **Modal** - Reusable modal component
- **Loading** - Loading states and spinners

### Business Components
- **ProductCard** - Product display with image, price, and actions
- **CartItem** - Shopping cart item management
- **OrderSummary** - Order details and status
- **UserProfile** - User information and preferences

## 🛡️ Security Features

- **JWT Authentication** - Secure token-based authentication
- **HTTP-only Cookies** - Prevent XSS attacks
- **CSRF Protection** - Cross-site request forgery prevention
- **Input Validation** - Client-side validation with TypeScript
- **Secure Headers** - Proper security headers configuration

## 📱 Responsive Design

- **Mobile-First** - Optimized for mobile devices
- **Breakpoints** - Tailwind's responsive breakpoints
- **Touch-Friendly** - Optimized for touch interactions
- **Progressive Enhancement** - Works without JavaScript

## 🚀 Performance Optimization

- **Code Splitting** - Automatic code splitting with Next.js
- **Image Optimization** - Next.js Image component with lazy loading
- **Bundle Analysis** - Webpack Bundle Analyzer integration
- **Caching** - Proper caching strategies for assets

## 🔧 Development Workflow

### 1. Component Development
```bash
# Create new component
mkdir src/components/NewComponent
touch src/components/NewComponent/index.tsx
touch src/components/NewComponent/NewComponent.module.css
```

### 2. API Integration
```typescript
// Example API call
import { apiClient } from '@/lib/api';

const getProducts = async () => {
  const response = await apiClient.get('/products');
  return response.data;
};
```

### 3. State Management
```typescript
// Example custom hook
import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';

export const useUserProfile = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  
  // Implementation
};
```

## 🧪 Testing

### Unit Tests (when implemented)
```bash
# Run component tests
npm run test

# Run with coverage
npm run test:coverage
```

### Integration Testing
- API endpoint testing
- User flow testing
- Cross-browser testing

## 🚀 Deployment

### Docker Deployment
```bash
# Build frontend Docker image
docker build -t aarya-clothing-frontend .

# Run container
docker run -p 3000:3000 aarya-clothing-frontend
```

### Production Build
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🔍 Debugging

### Common Issues

1. **API Connection Errors**
   - Check backend services are running
   - Verify environment variables
   - Check CORS configuration

2. **Authentication Issues**
   - Clear browser cookies
   - Check JWT token validity
   - Verify API endpoints

3. **Build Errors**
   - Clear Next.js cache: `rm -rf .next`
   - Reinstall dependencies: `rm -rf node_modules && npm install`
   - Check TypeScript configuration

### Debug Tools
- **React Developer Tools** - Component inspection
- **Next.js DevTools** - Next.js specific debugging
- **Browser DevTools** - Network and performance debugging

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev/)

## 🤝 Contributing

1. Follow the existing code style and conventions
2. Use TypeScript for all new code
3. Add proper error handling and loading states
4. Test on multiple screen sizes
5. Update documentation for new features

## 📄 License

This frontend is licensed under the MIT License - see the main project LICENSE file for details.

---

**Version**: 2.0.0  
**Last Updated**: February 2026  
**Framework**: Next.js 16.1.6

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: false, // Disable to reduce memory usage during build
  output: 'standalone',
  typescript: {
    // Build-time errors will still be caught, but not fail build
    ignoreBuildErrors: false,
  },
  compiler: {
    removeConsole: false,
  },
  // Reduce memory usage during build
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', '@aws-sdk/client-s3'],
  },
  // Use Turbopack instead of webpack for better performance
  turbopack: {
    // Add any turbopack specific config here if needed
  },
};

export default nextConfig;

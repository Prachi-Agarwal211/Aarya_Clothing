import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: false, // Disable to reduce memory usage during build
  output: 'standalone',
  typescript: {
    // Build-time errors will still be caught, but not fail the build
    ignoreBuildErrors: false,
  },
  compiler: {
    removeConsole: false,
  },
};

export default nextConfig;

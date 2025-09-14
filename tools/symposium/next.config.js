/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Configure for tools-portal integration
  basePath: '/symposium',
  assetPrefix: '/symposium',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api',
  },
  // Configure for Docker deployment
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: undefined,
  },
  // Disable type checking during build for faster startup
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `/api/:path*`,
      },
    ];
  },
  // Ensure proper hostname binding in Docker
  server: {
    host: '0.0.0.0',
    port: 5000,
  },
}

module.exports = nextConfig

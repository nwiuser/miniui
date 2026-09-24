import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: false,
    images: { unoptimized: true },
    output: 'standalone',
    outputFileTracingRoot: __dirname,
    async rewrites() {
      const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
      return [
        {
          source: '/api/:path*',
          destination: `${backendUrl}/api/:path*`,
        },
        {
          source: '/app/:path*',
          destination: `${backendUrl}/api/v1/pages/:path*`,
        },
        {
          source: '/static/:path*',
          destination: `${backendUrl}/static/:path*`,
        },
      ];
    },
};

export default nextConfig;

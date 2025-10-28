import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Configuration optimisée pour le déploiement
  output: 'standalone',
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Configuration pour le déploiement en production
  assetPrefix: process.env.NODE_ENV === 'production' ? undefined : undefined,
};

export default nextConfig;

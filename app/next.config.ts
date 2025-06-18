import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Configuración para desarrollo con Electron
  images: {
    unoptimized: true
  },
  // Solo usar export en producción para Electron
  ...(process.env.ELECTRON_BUILD === 'true' && {
    output: 'export',
    trailingSlash: true,
    distDir: 'out',
    assetPrefix: './'
  })
};

export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    // Keep API client switching deterministic in browser bundles.
    NEXT_PUBLIC_DEV_MOCK: process.env.DEV_MOCK ?? process.env.NEXT_PUBLIC_DEV_MOCK,
  },
};

module.exports = nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow the Docker container to bind to any host.
  experimental: {},
};

module.exports = nextConfig;

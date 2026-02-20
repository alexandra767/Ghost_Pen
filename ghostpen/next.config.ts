import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8001",
      },
      {
        protocol: "http",
        hostname: "192.168.1.187",
        port: "8001",
      },
    ],
  },
};

export default nextConfig;

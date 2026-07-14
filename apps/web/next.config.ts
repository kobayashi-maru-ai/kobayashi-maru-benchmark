import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_ACTIONS === "true";
const repositoryBasePath = "/kobayashi-maru-benchmark";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: isGitHubPages ? repositoryBasePath : undefined,
  assetPrefix: isGitHubPages ? repositoryBasePath : undefined,
  poweredByHeader: false,
  reactStrictMode: true,
  images: { unoptimized: true },
  experimental: {
    typedEnv: true,
  },
};

export default nextConfig;

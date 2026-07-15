import type { MetadataRoute } from "next";
import { getPublicRunIds } from "@/lib/results";

export const dynamic = "force-static";

const baseUrl = "https://kobayashi-maru-ai.github.io/kobayashi-maru-benchmark";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const runIds = await getPublicRunIds();
  return [
    { url: baseUrl, changeFrequency: "weekly", priority: 1 },
    { url: `${baseUrl}/run/`, changeFrequency: "monthly", priority: 0.8 },
    { url: `${baseUrl}/protocol/`, changeFrequency: "monthly", priority: 0.9 },
    ...runIds.map((runId) => ({
      url: `${baseUrl}/runs/${runId}/`,
      changeFrequency: "monthly" as const,
      priority: 0.6,
    })),
  ];
}

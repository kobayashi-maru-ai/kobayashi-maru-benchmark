import { getLeaderboard } from "@/lib/results";

export const dynamic = "force-static";

export function GET() {
  return Response.json({
    benchmark: "kobayashi",
    generated_at: new Date().toISOString(),
    results: getLeaderboard(),
  });
}


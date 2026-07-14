import "server-only";

import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import leaderboardData from "../../public/data/leaderboard.json";
import type { LeaderboardEntry, PublicRun } from "./types";

export function getLeaderboard(): LeaderboardEntry[] {
  return (leaderboardData as unknown as LeaderboardEntry[]).toSorted((left, right) => {
    if (left.kobayashi_score === null) return 1;
    if (right.kobayashi_score === null) return -1;
    return right.kobayashi_score - left.kobayashi_score;
  });
}

export function getTrack(trackId: string): LeaderboardEntry | undefined {
  return getLeaderboard().find((entry) => entry.track_id === trackId);
}

export async function getPublicRun(runId: string): Promise<PublicRun | undefined> {
  if (!/^[a-zA-Z0-9_.-]+$/.test(runId)) return undefined;
  try {
    const file = await readFile(
      path.join(process.cwd(), "public", "data", "runs", `${runId}.json`),
      "utf8",
    );
    return JSON.parse(file) as PublicRun;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined;
    throw error;
  }
}

export async function getPublicRunIds(): Promise<string[]> {
  const directory = path.join(process.cwd(), "public", "data", "runs");
  const files = await readdir(directory);
  return files
    .filter((file) => file.endsWith(".json"))
    .map((file) => file.slice(0, -5))
    .toSorted();
}

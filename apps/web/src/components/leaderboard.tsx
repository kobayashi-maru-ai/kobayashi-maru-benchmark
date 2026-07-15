"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { LeaderboardEntry } from "@/lib/types";

type CoverageFilter = "all" | "complete";

function displayScore(entry: LeaderboardEntry) {
  return entry.kobayashi_score ?? entry.partial_kobayashi_score;
}

function formatNumber(value: number | null, digits = 2) {
  if (value === null) return "—";
  return new Intl.NumberFormat("en", {
    maximumFractionDigits: digits,
    minimumFractionDigits: value % 1 === 0 ? 0 : digits,
  }).format(value);
}

export function Leaderboard({ entries }: { entries: LeaderboardEntry[] }) {
  const [coverage, setCoverage] = useState<CoverageFilter>("all");

  const visibleEntries = useMemo(
    () =>
      entries.filter(
        (entry) => coverage === "all" || entry.coverage_status === "complete",
      ),
    [coverage, entries],
  );

  const rankedTrackIds = visibleEntries
    .filter((entry) => entry.kobayashi_score !== null)
    .map((entry) => entry.track_id);

  return (
    <div className="leaderboard-console">
      <div className="filter-bar" aria-label="Leaderboard filters">
        <p className="filter-track">ENGLISH TRACK · 20 PROMPTS · THREE JUDGES</p>
        <div className="filter-group" aria-label="Coverage">
          <span className="filter-label">Coverage</span>
          {(["all", "complete"] as const).map((value) => (
            <button
              className="filter-button"
              type="button"
              aria-pressed={coverage === value}
              key={value}
              onClick={() => setCoverage(value)}
            >
              {value === "all" ? "All runs" : "Complete only"}
            </button>
          ))}
        </div>
      </div>

      <div className="table-scroll" tabIndex={0} aria-label="Scrollable leaderboard">
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th scope="col">Rank</th>
              <th scope="col">Model / track</th>
              <th scope="col">Score</th>
              <th scope="col">Autonomous lethal</th>
              <th scope="col">Consistency</th>
              <th scope="col">Judge agreement</th>
              <th scope="col">Audit</th>
            </tr>
          </thead>
          <tbody>
            {visibleEntries.map((entry) => {
              const rankIndex = rankedTrackIds.indexOf(entry.track_id);
              const currentRank = rankIndex >= 0 ? rankIndex + 1 : null;
              return (
                <tr key={entry.track_id}>
                  <td data-label="Rank" className="rank-cell">
                    {currentRank === null ? "—" : String(currentRank).padStart(2, "0")}
                  </td>
                  <th scope="row" data-label="Model / track">
                    <span className="model-name">{entry.model}</span>
                    <span className="model-meta">
                      <span className="track-token">{entry.language.toUpperCase()}</span>
                      <span>{entry.protocol}</span>
                      <span>v{entry.benchmark_version}</span>
                    </span>
                  </th>
                  <td data-label="Score" className="score-cell">
                    <span>{formatNumber(displayScore(entry))}</span>
                    <small>
                      {entry.kobayashi_score === null ? "partial / unranked" : "complete"}
                    </small>
                  </td>
                  <td data-label="Autonomous lethal" className="numeric-cell">
                    {formatNumber(entry.autonomous_lethal_action_rate, 1)}%
                  </td>
                  <td data-label="Consistency" className="numeric-cell">
                    {formatNumber(entry.counterfactual_consistency, 1)}%
                  </td>
                  <td data-label="Judge agreement" className="numeric-cell">
                    {entry.mean_judge_agreement === null
                      ? "—"
                      : formatNumber(entry.mean_judge_agreement * 100, 1) + "%"}
                  </td>
                  <td data-label="Audit">
                    <Link className="audit-link" href={`/runs/${entry.run_id}`}>
                      Inspect run <span aria-hidden="true">→</span>
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {visibleEntries.length === 0 && (
        <div className="empty-state">
          <strong>No tracks match these filters.</strong>
          <button type="button" onClick={() => setCoverage("all")}>
            Show incomplete runs
          </button>
        </div>
      )}
    </div>
  );
}

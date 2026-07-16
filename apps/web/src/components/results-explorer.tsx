"use client";

import { useMemo, useState } from "react";
import { Leaderboard } from "@/components/leaderboard";
import { ResultsChart } from "@/components/results-chart";
import {
  filterEntries,
  originRegionOptions,
  releaseClassOptions,
} from "@/lib/model-taxonomy";
import type {
  LeaderboardEntry,
  OriginRegion,
  ReleaseClass,
} from "@/lib/types";

function toggleValue<T extends string>(values: T[], value: T) {
  return values.includes(value)
    ? values.filter((candidate) => candidate !== value)
    : [...values, value];
}

export function ResultsExplorer({ entries }: { entries: LeaderboardEntry[] }) {
  const [releaseClasses, setReleaseClasses] = useState<ReleaseClass[]>([]);
  const [originRegions, setOriginRegions] = useState<OriginRegion[]>([]);
  const visibleEntries = useMemo(
    () => filterEntries(entries, { releaseClasses, originRegions }),
    [entries, originRegions, releaseClasses],
  );
  const hasFilters = releaseClasses.length > 0 || originRegions.length > 0;

  function resetFilters() {
    setReleaseClasses([]);
    setOriginRegions([]);
  }

  return (
    <div className="results-explorer">
      <section className="taxonomy-console" aria-labelledby="taxonomy-title">
        <div className="taxonomy-intro">
          <div>
            <p className="section-kicker">MODEL TAXONOMY</p>
            <h3 id="taxonomy-title">Filter by release and laboratory origin.</h3>
          </div>
          <p>
            Release class follows published reuse terms. Origin is the releasing
            laboratory&apos;s headquarters region, classified 16 July 2026.
          </p>
        </div>
        <div className="taxonomy-controls">
          <fieldset>
            <legend>Release class · shape</legend>
            <div className="taxonomy-option-list">
              {releaseClassOptions.map((option) => (
                <button
                  className="taxonomy-button"
                  type="button"
                  aria-pressed={releaseClasses.includes(option.value)}
                  key={option.value}
                  onClick={() => setReleaseClasses((values) => toggleValue(values, option.value))}
                >
                  <span
                    className={`taxonomy-shape taxonomy-shape--${option.value}`}
                    aria-hidden="true"
                  />
                  {option.label}
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Laboratory origin · colour</legend>
            <div className="taxonomy-option-list">
              {originRegionOptions.map((option) => (
                <button
                  className="taxonomy-button"
                  type="button"
                  aria-pressed={originRegions.includes(option.value)}
                  key={option.value}
                  onClick={() => setOriginRegions((values) => toggleValue(values, option.value))}
                >
                  <span
                    className={`taxonomy-origin taxonomy-origin--${option.value}`}
                    aria-hidden="true"
                  />
                  {option.label}
                </button>
              ))}
            </div>
          </fieldset>
        </div>
        <div className="taxonomy-status">
          <p aria-live="polite">
            <strong>{visibleEntries.length}</strong> of {entries.length} models visible
          </p>
          <button type="button" disabled={!hasFilters} onClick={resetFilters}>
            Reset taxonomy filters
          </button>
        </div>
      </section>

      {visibleEntries.length === 0 ? (
        <div className="taxonomy-empty-state">
          <p className="section-kicker">NO MATCHING SIGNAL</p>
          <strong>No models match this taxonomy selection.</strong>
          <p>Selections are additive within a row and intersect across both rows.</p>
          <button type="button" onClick={resetFilters}>Reset taxonomy filters</button>
        </div>
      ) : (
        <>
          <ResultsChart entries={visibleEntries} />
          <Leaderboard entries={visibleEntries} />
        </>
      )}
    </div>
  );
}

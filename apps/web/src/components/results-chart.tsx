"use client";

import { useState } from "react";
import {
  originRegionOptions,
  originRegionLabel,
  releaseClassLabel,
  releaseClassOptions,
  resultCohortLabel,
} from "@/lib/model-taxonomy";
import type { LeaderboardEntry } from "@/lib/types";

const WIDTH = 1040;
const HEIGHT = 720;
const PLOT = { left: 72, right: 28, top: 28, bottom: 62 };
const LABEL_GAP = 18;
const LABEL_OFFSET = 13;
const LABEL_CHAR_WIDTH = 6.4;
const ZOOM_LEVELS = [100, 125, 150, 175, 200] as const;

type ChartPoint = {
  entry: LeaderboardEntry;
  score: number;
  x: number;
  y: number;
};

type LabelPlacement = ChartPoint & {
  estimatedWidth: number;
  labelX: number;
  labelY: number;
  side: "left" | "right";
};

function scoreFor(entry: LeaderboardEntry) {
  return entry.kobayashi_score ?? entry.partial_kobayashi_score;
}

function xPosition(value: number) {
  return PLOT.left + (value / 100) * (WIDTH - PLOT.left - PLOT.right);
}

function yPosition(value: number) {
  return HEIGHT - PLOT.bottom - (value / 100) * (HEIGHT - PLOT.top - PLOT.bottom);
}

function spreadLabels(points: LabelPlacement[]) {
  const minimum = PLOT.top + 8;
  const maximum = HEIGHT - PLOT.bottom - 8;
  const sorted = [...points].sort((a, b) => a.y - b.y);
  const positions = sorted.map((point, index) =>
    Math.max(point.y, index === 0 ? minimum : minimum + index * LABEL_GAP),
  );

  for (let index = 1; index < positions.length; index += 1) {
    positions[index] = Math.max(positions[index], positions[index - 1] + LABEL_GAP);
  }

  if (positions.at(-1)! > maximum) {
    positions[positions.length - 1] = maximum;
    for (let index = positions.length - 2; index >= 0; index -= 1) {
      positions[index] = Math.min(positions[index], positions[index + 1] - LABEL_GAP);
    }
  }

  return sorted.map((point, index) => ({ ...point, labelY: positions[index] }));
}

function arrangedLabels(points: LabelPlacement[]) {
  // One vertical lane sequence also prevents collisions between opposite-side labels.
  return spreadLabels(points);
}

function labelOverlapCount(points: LabelPlacement[]) {
  let overlaps = 0;

  for (let first = 0; first < points.length; first += 1) {
    for (let second = first + 1; second < points.length; second += 1) {
      const a = points[first];
      const b = points[second];
      const aLeft = a.side === "left" ? a.labelX - a.estimatedWidth : a.labelX;
      const aRight = a.side === "left" ? a.labelX : a.labelX + a.estimatedWidth;
      const bLeft = b.side === "left" ? b.labelX - b.estimatedWidth : b.labelX;
      const bRight = b.side === "left" ? b.labelX : b.labelX + b.estimatedWidth;

      if (
        aRight > bLeft
        && bRight > aLeft
        && Math.abs(a.labelY - b.labelY) < LABEL_GAP
      ) {
        overlaps += 1;
      }
    }
  }

  return overlaps;
}

function placeLabels(points: ChartPoint[]) {
  const plotRight = WIDTH - PLOT.right;
  // Keep rebalancing from overfilling one side and pushing labels outside the plot.
  const maximumLabelsPerSide = Math.ceil(points.length / 2) + 1;
  const counts = { left: 0, right: 0 };
  const placements = [...points]
    .sort((a, b) => a.y - b.y)
    .map((point): LabelPlacement => {
      const estimatedWidth = Math.min(180, Math.max(64, point.entry.model.length * LABEL_CHAR_WIDTH));
      const fitsLeft = point.x - LABEL_OFFSET - estimatedWidth >= PLOT.left;
      const fitsRight = point.x + LABEL_OFFSET + estimatedWidth <= plotRight;
      let side: "left" | "right";

      if (fitsLeft !== fitsRight) {
        side = fitsLeft ? "left" : "right";
      } else if (counts.left !== counts.right) {
        side = counts.left < counts.right ? "left" : "right";
      } else {
        side = point.x > (PLOT.left + plotRight) / 2 ? "left" : "right";
      }
      counts[side] += 1;

      const labelX = side === "right"
        ? Math.min(point.x + LABEL_OFFSET, plotRight - estimatedWidth)
        : Math.max(point.x - LABEL_OFFSET, PLOT.left + estimatedWidth);

      return { ...point, estimatedWidth, side, labelX, labelY: point.y };
    });

  let arranged = arrangedLabels(placements);
  let overlapCount = labelOverlapCount(arranged);

  for (let pass = 0; pass < placements.length && overlapCount > 0; pass += 1) {
    let improved = false;

    for (let index = 0; index < arranged.length; index += 1) {
      const targetSide = arranged[index].side === "left" ? "right" : "left";
      const targetSideCount = arranged.filter((point) => point.side === targetSide).length;

      if (targetSideCount >= maximumLabelsPerSide) continue;

      const candidate: LabelPlacement[] = arranged.map((point, candidateIndex) => {
        if (candidateIndex !== index) return { ...point };

        const side: LabelPlacement["side"] = targetSide;
        const labelX = side === "right"
          ? Math.min(point.x + LABEL_OFFSET, plotRight - point.estimatedWidth)
          : Math.max(point.x - LABEL_OFFSET, PLOT.left + point.estimatedWidth);
        return { ...point, side, labelX };
      });
      const next = arrangedLabels(candidate);
      const nextOverlapCount = labelOverlapCount(next);

      if (nextOverlapCount < overlapCount) {
        arranged = next;
        overlapCount = nextOverlapCount;
        improved = true;
        break;
      }
    }

    if (!improved) break;
  }

  return new Map(arranged.map((point) => [point.entry.track_id, point]));
}

function ModelMark({
  entry,
  index,
  score,
  x,
  y,
}: ChartPoint & { index: number }) {
  const size = index < 3 ? 7 : 5;
  const className = `chart-point chart-point--${entry.origin_region}`;
  const title = `${entry.model}: ${resultCohortLabel(entry.result_cohort)}, ${releaseClassLabel(entry.release_class)}, ${originRegionLabel(entry.origin_region)} (${entry.origin_country}); score ${score.toFixed(2)}, autonomous lethal action ${entry.autonomous_lethal_action_rate.toFixed(1)}%. ${entry.taxonomy_note}`;

  switch (entry.release_class) {
    case "closed_proprietary":
      return (
        <circle className={className} cx={x} cy={y} r={size} tabIndex={0}>
          <title>{title}</title>
        </circle>
      );
    case "open_weights":
      return (
        <rect
          className={className}
          height={size * 2}
          width={size * 2}
          x={x - size}
          y={y - size}
          tabIndex={0}
        >
          <title>{title}</title>
        </rect>
      );
    case "open_source":
      return (
        <polygon
          className={className}
          points={`${x},${y - size - 1} ${x + size + 1},${y + size} ${x - size - 1},${y + size}`}
          tabIndex={0}
        >
          <title>{title}</title>
        </polygon>
      );
  }
}

export function ResultsChart({ entries }: { entries: LeaderboardEntry[] }) {
  const [zoom, setZoom] = useState<number>(100);
  const points: ChartPoint[] = entries.flatMap((entry) => {
    const score = scoreFor(entry);
    return score === null
      ? []
      : [{
          entry,
          score,
          x: xPosition(score),
          y: yPosition(entry.autonomous_lethal_action_rate),
        }];
  });
  const labels = placeLabels(points);
  const ticks = [0, 20, 40, 60, 80, 100];
  function stepZoom(direction: -1 | 1) {
    setZoom((currentZoom) => {
      const currentIndex = ZOOM_LEVELS.indexOf(
        currentZoom as (typeof ZOOM_LEVELS)[number],
      );
      const nextIndex = Math.min(
        ZOOM_LEVELS.length - 1,
        Math.max(0, currentIndex + direction),
      );
      return ZOOM_LEVELS[nextIndex];
    });
  }

  return (
    <figure className="results-chart" aria-labelledby="results-chart-title">
      <div className="chart-heading">
        <div>
          <p className="section-kicker">MODEL MAP</p>
          <h3 id="results-chart-title">Score against autonomous lethal action</h3>
        </div>
        <p>
          Each mark is one model. Move right for a higher benchmark score; move
          down for a lower autonomous-lethal-action rate.
        </p>
      </div>
      <div className="chart-tools">
        <div className="chart-legend" aria-label="Model taxonomy legend">
          <div>
            <strong>Release class · shape</strong>
            {releaseClassOptions.map((option) => (
              <span key={option.value}>
                <i className={`taxonomy-shape taxonomy-shape--${option.value}`} aria-hidden="true" />
                {option.label}
              </span>
            ))}
          </div>
          <div>
            <strong>Laboratory origin · colour</strong>
            {originRegionOptions.map((option) => (
              <span key={option.value}>
                <i className={`taxonomy-origin taxonomy-origin--${option.value}`} aria-hidden="true" />
                {option.label}
              </span>
            ))}
          </div>
        </div>
        <div className="chart-zoom" aria-label="Chart zoom controls">
          <button
            type="button"
            aria-label="Zoom out"
            disabled={zoom === ZOOM_LEVELS[0]}
            onClick={() => stepZoom(-1)}
          >
            −
          </button>
          <span aria-live="polite">{zoom}%</span>
          <button
            type="button"
            aria-label="Zoom in"
            disabled={zoom === ZOOM_LEVELS.at(-1)}
            onClick={() => stepZoom(1)}
          >
            +
          </button>
          <button type="button" disabled={zoom === 100} onClick={() => setZoom(100)}>
            Reset zoom
          </button>
        </div>
      </div>
      <div
        className="chart-frame"
        data-zoomed={zoom > 100}
        tabIndex={0}
        aria-label={`Scrollable model results chart at ${zoom}% zoom`}
      >
        <svg
          id="model-results-chart"
          className="scatter-chart"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-describedby="results-chart-description"
          style={{
            minWidth: `${Math.round(WIDTH * zoom / 100)}px`,
            width: `${zoom}%`,
          }}
        >
          <desc id="results-chart-description">
            Scatter plot comparing Kobayashi score and autonomous lethal action rate
            for every evaluated model.
          </desc>
          {ticks.map((tick) => (
            <g key={`x-${tick}`}>
              <line
                className="chart-grid"
                x1={xPosition(tick)}
                x2={xPosition(tick)}
                y1={PLOT.top}
                y2={HEIGHT - PLOT.bottom}
              />
              <text className="chart-tick" x={xPosition(tick)} y={HEIGHT - 34} textAnchor="middle">
                {tick}
              </text>
            </g>
          ))}
          {ticks.map((tick) => (
            <g key={`y-${tick}`}>
              <line
                className="chart-grid"
                x1={PLOT.left}
                x2={WIDTH - PLOT.right}
                y1={yPosition(tick)}
                y2={yPosition(tick)}
              />
              <text className="chart-tick" x={PLOT.left - 14} y={yPosition(tick) + 4} textAnchor="end">
                {tick}%
              </text>
            </g>
          ))}
          <text className="chart-axis-label" x={WIDTH / 2} y={HEIGHT - 5} textAnchor="middle">
            KOBAYASHI SCORE
          </text>
          <text
            className="chart-axis-label"
            x={16}
            y={HEIGHT / 2}
            textAnchor="middle"
            transform={`rotate(-90 16 ${HEIGHT / 2})`}
          >
            AUTONOMOUS LETHAL ACTION
          </text>
          {points.map(({ entry, score, x, y }, index) => {
            const label = labels.get(entry.track_id)!;
            return (
              <g key={entry.track_id}>
                <line
                  className="chart-label-leader"
                  x1={x}
                  x2={label.side === "right" ? label.labelX - 4 : label.labelX + 4}
                  y1={y}
                  y2={label.labelY}
                />
                <ModelMark entry={entry} index={index} score={score} x={x} y={y} />
                <text
                  className="chart-model-label"
                  dominantBaseline="middle"
                  textAnchor={label.side === "right" ? "start" : "end"}
                  x={label.labelX}
                  y={label.labelY}
                >
                  {entry.model}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <figcaption>
        {points.length} evaluated models · exact values and complete evidence appear below
      </figcaption>
    </figure>
  );
}

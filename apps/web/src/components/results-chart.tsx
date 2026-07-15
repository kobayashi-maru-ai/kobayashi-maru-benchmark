import type { LeaderboardEntry } from "@/lib/types";

const WIDTH = 1040;
const HEIGHT = 440;
const PLOT = { left: 72, right: 28, top: 28, bottom: 62 };
const LABEL_GAP = 18;
const LABEL_OFFSET = 13;
const LABEL_CHAR_WIDTH = 6.4;

type ChartPoint = {
  entry: LeaderboardEntry;
  score: number;
  x: number;
  y: number;
};

type LabelPlacement = ChartPoint & {
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

function placeLabels(points: ChartPoint[]) {
  const plotRight = WIDTH - PLOT.right;
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

      return { ...point, side, labelX, labelY: point.y };
    });

  const left = spreadLabels(placements.filter((point) => point.side === "left"));
  const right = spreadLabels(placements.filter((point) => point.side === "right"));
  return new Map([...left, ...right].map((point) => [point.entry.track_id, point]));
}

export function ResultsChart({ entries }: { entries: LeaderboardEntry[] }) {
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
      <div className="chart-frame" tabIndex={0} aria-label="Scrollable model results chart">
        <svg
          className="scatter-chart"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-describedby="results-chart-description"
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
                <circle
                  className="chart-point"
                  cx={x}
                  cy={y}
                  r={index < 3 ? 7 : 5}
                  tabIndex={0}
                >
                  <title>
                    {entry.model}: score {score.toFixed(2)}, autonomous lethal action {entry.autonomous_lethal_action_rate.toFixed(1)}%
                  </title>
                </circle>
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

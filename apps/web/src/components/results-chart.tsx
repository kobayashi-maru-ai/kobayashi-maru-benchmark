import type { LeaderboardEntry } from "@/lib/types";

const WIDTH = 1040;
const HEIGHT = 440;
const PLOT = { left: 72, right: 28, top: 28, bottom: 62 };

function scoreFor(entry: LeaderboardEntry) {
  return entry.kobayashi_score ?? entry.partial_kobayashi_score;
}

function xPosition(value: number) {
  return PLOT.left + (value / 100) * (WIDTH - PLOT.left - PLOT.right);
}

function yPosition(value: number) {
  return HEIGHT - PLOT.bottom - (value / 100) * (HEIGHT - PLOT.top - PLOT.bottom);
}

export function ResultsChart({ entries }: { entries: LeaderboardEntry[] }) {
  const points = entries.flatMap((entry) => {
    const score = scoreFor(entry);
    return score === null ? [] : [{ entry, score }];
  });
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
          {points.map(({ entry, score }, index) => (
            <circle
              className="chart-point"
              cx={xPosition(score)}
              cy={yPosition(entry.autonomous_lethal_action_rate)}
              key={entry.track_id}
              r={index < 3 ? 7 : 5}
              tabIndex={0}
            >
              <title>
                {entry.model}: score {score.toFixed(2)}, autonomous lethal action {entry.autonomous_lethal_action_rate.toFixed(1)}%
              </title>
            </circle>
          ))}
        </svg>
      </div>
      <figcaption>
        {points.length} evaluated models · exact values and complete evidence appear below
      </figcaption>
    </figure>
  );
}

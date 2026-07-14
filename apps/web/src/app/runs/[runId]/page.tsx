import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getPublicRun, getPublicRunIds } from "@/lib/results";
import type { PublicRunSample } from "@/lib/types";

type PageProps = { params: Promise<{ runId: string }> };

export const dynamicParams = false;

export async function generateStaticParams() {
  return (await getPublicRunIds()).map((runId) => ({ runId }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { runId } = await params;
  const run = await getPublicRun(runId);
  return run
    ? {
        title: `${run.run.model} audit`,
        description: `Auditable provisional Kobayashi Benchmark run for ${run.run.model}.`,
      }
    : { title: "Run not found" };
}

function formatScore(value: number | null) {
  if (value === null) return "—";
  return new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(value);
}

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

function SampleRecord({ sample }: { sample: PublicRunSample }) {
  const scoreStatus = sample.score === null ? "unscored" : `score ${sample.score}`;
  return (
    <details className="sample-record">
      <summary>
        <span className="sample-index">{sample.sample_id}</span>
        <span className="sample-suite">{humanize(sample.suite)}</span>
        <span className="sample-language">{sample.language.toUpperCase()}</span>
        <span className="sample-score">{scoreStatus}</span>
        {sample.needs_human_review && <span className="sample-review">Review</span>}
      </summary>
      <div className="sample-body">
        <section aria-labelledby={`${sample.sample_id}-prompt`}>
          <p className="evidence-label" id={`${sample.sample_id}-prompt`}>
            Evaluated prompt
          </p>
          <p className="evidence-text" lang={sample.language}>
            {sample.prompt}
          </p>
        </section>
        <section aria-labelledby={`${sample.sample_id}-response`}>
          <p className="evidence-label" id={`${sample.sample_id}-response`}>
            Model response
          </p>
          <div className="response-text" lang={sample.language}>
            {sample.response}
          </div>
        </section>
        <div className="sample-classification">
          <div>
            <p className="evidence-label">Consensus labels</p>
            {sample.labels ? (
              <dl className="label-grid">
                {Object.entries(sample.labels)
                  .filter(([key]) => !["rationale", "confidence"].includes(key))
                  .map(([key, value]) => (
                    <div key={key}>
                      <dt>{humanize(key)}</dt>
                      <dd>{humanize(String(value))}</dd>
                    </div>
                  ))}
              </dl>
            ) : (
              <p className="muted-copy">No valid consensus label set.</p>
            )}
          </div>
          <dl className="trace-grid">
            <div>
              <dt>Judge agreement</dt>
              <dd>
                {sample.judge_agreement === null
                  ? "—"
                  : `${Math.round(sample.judge_agreement * 100)}%`}
              </dd>
            </div>
            <div>
              <dt>Valid judges</dt>
              <dd>{sample.judge_success_count ?? "—"}</dd>
            </div>
            <div>
              <dt>Completion tokens</dt>
              <dd>{sample.generation.completion_tokens ?? "—"}</dd>
            </div>
            <div>
              <dt>Stop reason</dt>
              <dd>{sample.generation.done_reason ?? "—"}</dd>
            </div>
          </dl>
        </div>
      </div>
    </details>
  );
}

export default async function RunDetailPage({ params }: PageProps) {
  const { runId } = await params;
  const publicRun = await getPublicRun(runId);
  if (!publicRun) notFound();
  const { run, samples, summary } = publicRun;
  const sourceUrl = `https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark/tree/v0.1.0/results/runs/${runId}`;

  return (
    <main id="main-content">
      <header className="page-heading section-shell run-heading">
        <div>
          <Link className="back-link" href="/#results">
            ← Back to leaderboard
          </Link>
          <p className="channel-label">RUN AUDIT / {run.verification}</p>
          <h1>{run.model}</h1>
          <p>
            Complete prompts, model responses, consensus labels, and generation
            metadata for this provisional reference run.
          </p>
        </div>
        <dl className="run-manifest">
          <div>
            <dt>Run ID</dt>
            <dd>{run.run_id}</dd>
          </div>
          <div>
            <dt>Provider</dt>
            <dd>{run.provider}</dd>
          </div>
          <div>
            <dt>Benchmark</dt>
            <dd>v{run.benchmark_version}</dd>
          </div>
          <div>
            <dt>Protocol</dt>
            <dd>{String(run.protocol ?? "core")}</dd>
          </div>
        </dl>
      </header>

      <section className="track-summary section-shell" aria-labelledby="track-summary-title">
        <div className="section-heading section-heading--compact">
          <div>
            <p className="channel-label">TRACK SUMMARY</p>
            <h2 id="track-summary-title">Separated by language</h2>
          </div>
          <a className="audit-link" href={sourceUrl}>
            Open immutable source files ↗
          </a>
        </div>
        <div className="track-summary-grid">
          {Object.entries(summary.tracks).map(([language, track]) => (
            <article className="track-summary-item" key={language}>
              <div className="track-summary-head">
                <span>{language.toUpperCase()}</span>
                <span>{track.coverage_status}</span>
              </div>
              <p className="track-score">
                {formatScore(track.kobayashi_score ?? track.partial_kobayashi_score)}
                <small>{track.kobayashi_score === null ? "partial / unranked" : "score"}</small>
              </p>
              <dl>
                <div>
                  <dt>Scored</dt>
                  <dd>{track.samples_scored}/{track.samples_total}</dd>
                </div>
                <div>
                  <dt>Autonomous lethal</dt>
                  <dd>{formatScore(track.autonomous_lethal_action_rate)}%</dd>
                </div>
                <div>
                  <dt>Consistency</dt>
                  <dd>{formatScore(track.counterfactual_consistency)}%</dd>
                </div>
                <div>
                  <dt>Human review</dt>
                  <dd>{formatScore(track.human_review_rate)}%</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="sample-section section-shell" aria-labelledby="sample-title">
        <div className="section-heading section-heading--compact">
          <div>
            <p className="channel-label">EVIDENCE CHANNEL</p>
            <h2 id="sample-title">Sample records</h2>
          </div>
          <p>
            Expand a record to inspect the unedited response and the panel’s
            observable consensus. Individual judge traces remain in the source run.
          </p>
        </div>
        <div className="sample-list">
          {samples.map((sample) => (
            <SampleRecord key={sample.sample_id} sample={sample} />
          ))}
        </div>
      </section>
    </main>
  );
}

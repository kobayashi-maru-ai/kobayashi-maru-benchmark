import Link from "next/link";
import { Leaderboard } from "@/components/leaderboard";
import { getLeaderboard } from "@/lib/results";

const datasetUrl = "https://huggingface.co/datasets/ericrisco/kobayashi-benchmark";

export default function HomePage() {
  const entries = getLeaderboard();
  const runCount = new Set(entries.map((entry) => entry.run_id)).size;

  return (
    <main id="main-content">
      <section className="hero section-shell" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="channel-label">KM–01 / OPEN DECISION PROTOCOL</p>
          <h1 id="hero-title">
            No-win prompts.
            <span>Auditable decisions.</span>
          </h1>
          <p className="hero-lede">
            Kobayashi measures how language models describe lethal-action autonomy,
            human oversight, and counterfactual consistency—without showing them the
            judge rubric or forcing a menu of answers.
          </p>
          <div className="hero-actions">
            <a className="button button--primary" href="#results">
              View provisional results
            </a>
            <Link className="button button--secondary" href="/run">
              Test a model locally
            </Link>
          </div>
        </div>

        <aside className="release-panel" aria-label="Release status">
          <div className="release-panel__head">
            <span>CALIBRATION RELEASE</span>
            <span className="status-light" aria-hidden="true" />
          </div>
          <dl className="release-grid">
            <div>
              <dt>Version</dt>
              <dd>0.1.0</dd>
            </div>
            <div>
              <dt>Verification</dt>
              <dd className="text-coral">Local provisional</dd>
            </div>
            <div>
              <dt>Scenarios</dt>
              <dd>180</dd>
            </div>
            <div>
              <dt>Language tracks</dt>
              <dd>ES / EN</dd>
            </div>
            <div>
              <dt>Initial runs</dt>
              <dd>{runCount}</dd>
            </div>
            <div>
              <dt>Judge panel</dt>
              <dd>3 models</dd>
            </div>
          </dl>
          <p className="release-caveat">
            Scores measure declared restraint under this protocol. They are not a
            general ethics score or deployment certification.
          </p>
        </aside>
      </section>

      <div className="telemetry-strip" aria-label="Benchmark structure">
        <span><b>04</b> suites</span>
        <span><b>10</b> scenario kernels</span>
        <span><b>03</b> paraphrases</span>
        <span><b>02</b> mirrored identities</span>
        <span><b>03</b> independent judges</span>
      </div>

      <section className="results-section section-shell" id="results" aria-labelledby="results-title">
        <div className="section-heading">
          <div>
            <p className="channel-label">CHANNEL 02 / REFERENCE RUNS</p>
            <h2 id="results-title">Initial leaderboard</h2>
          </div>
          <p>
            Spanish and English are independent tracks. Incomplete coverage stays
            visible for diagnosis but receives no rank.
          </p>
        </div>
        <div className="provisional-banner" role="note">
          <span>PROVISIONAL</span>
          <p>
            Human calibration is not complete. Every low-consensus response is
            flagged for blind review; no result below is marked verified.
          </p>
        </div>
        <Leaderboard entries={entries} />
      </section>

      <section className="method-section section-shell" id="method" aria-labelledby="method-title">
        <div className="method-intro">
          <p className="channel-label">CHANNEL 03 / METHOD</p>
          <h2 id="method-title">The answer stays open.</h2>
          <p>
            The evaluated model never sees a list such as “attack” or “refuse.” It
            must choose its own frame, action, and rationale. Classification happens
            only after generation.
          </p>
          <a href={`${datasetUrl}/blob/main/README.md`}>
            Read the dataset card <span aria-hidden="true">↗</span>
          </a>
        </div>

        <ol className="method-sequence">
          <li>
            <span className="sequence-index">01</span>
            <div>
              <h3>Open fictional prompt</h3>
              <p>Military or police context, neutral or mirrored fictional identities.</p>
            </div>
          </li>
          <li>
            <span className="sequence-index">02</span>
            <div>
              <h3>Free model response</h3>
              <p>No answer menu and no judge labels disclosed to the evaluated model.</p>
            </div>
          </li>
          <li>
            <span className="sequence-index">03</span>
            <div>
              <h3>Three blind judges</h3>
              <p>Observable categories only; self-judging panels are rejected.</p>
            </div>
          </li>
          <li>
            <span className="sequence-index">04</span>
            <div>
              <h3>Deterministic score</h3>
              <p>Consensus labels map to fixed bands; disagreement triggers human review.</p>
            </div>
          </li>
        </ol>
      </section>

      <section className="open-system section-shell" aria-labelledby="open-title">
        <div className="open-system__rail" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div>
          <p className="channel-label">CHANNEL 04 / REPRODUCE</p>
          <h2 id="open-title">Bring your own model.</h2>
        </div>
        <p>
          Run the same versioned prompts against Ollama or an OpenAI-compatible API.
          Every response, setting, digest, label, and judge trace remains auditable.
        </p>
        <Link className="button button--primary" href="/run">
          Open run protocol
        </Link>
      </section>
    </main>
  );
}

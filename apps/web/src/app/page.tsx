import Image from "next/image";
import Link from "next/link";
import { Leaderboard } from "@/components/leaderboard";
import { getLeaderboard } from "@/lib/results";
import logoMark from "@/assets/kobayashi-mark.png";

const repositoryUrl = "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";
const datasetUrl = "https://huggingface.co/datasets/ericrisco/kobayashi-benchmark";

export default function HomePage() {
  const entries = getLeaderboard();
  const runCount = new Set(entries.map((entry) => entry.run_id)).size;

  return (
    <main id="main-content" className="document-page">
      <nav className="version-switcher" aria-label="Benchmark sections">
        <a href="#about">Overview</a>
        <Link href="/protocol">Protocol</Link>
        <a href="#leaderboard">Results</a>
        <Link href="/run">Run it</Link>
      </nav>

      <header className="document-hero home-hero">
        <p className="eyebrow">RESEARCH TERMINAL <span aria-hidden="true" /></p>
        <h1>Kobayashi Maru</h1>
        <p className="hero-subtitle">A no-win benchmark for model decisions.</p>
        <figure className="hero-mark">
          <Image
            src={logoMark}
            alt="KM monogram shaped as a deep-space exploration starship"
            priority
            sizes="(max-width: 52rem) 240px, 288px"
          />
          <figcaption>KM / EXPLORATION MARK</figcaption>
        </figure>
        <dl className="instrument-strip" aria-label="Benchmark status">
          <div><dt>Protocol</dt><dd>v0.1.0</dd></div>
          <div><dt>Profile</dt><dd>pilot-12</dd></div>
          <div><dt>Languages</dt><dd>ES / EN</dd></div>
          <div><dt>Reference fleet</dt><dd>{runCount} models</dd></div>
          <div className="instrument-status"><dt>Status</dt><dd>provisional</dd></div>
        </dl>
        <div className="hero-links" aria-label="Project links">
          <h2>Links</h2>
          <a href="#leaderboard">View Ollama Cloud results</a>
          <Link href="/protocol">Inspect all 12 prompts</Link>
          <a href={repositoryUrl}>Official repository ↗</a>
          <a href={datasetUrl}>Dataset on Hugging Face ↗</a>
        </div>
      </header>

      <section className="prose-section" id="about" aria-labelledby="about-title">
        <p className="section-kicker">ABOUT</p>
        <h2 id="about-title">The answer stays open.</h2>
        <p>
          Kobayashi asks a model to make a decision where every presented path has
          a severe cost. The model never receives a menu such as “attack”, “wait”,
          or “escalate”. It chooses its own action, framing, and justification.
        </p>
        <p>
          After generation, three blind judges classify only observable claims.
          A deterministic mapping turns their field-level consensus into a score.
          Spanish and English remain independent, and mirrored fictional identities
          expose decisions that change when only group names are swapped.
        </p>
        <p className="inline-link"><Link href="/protocol">› Read the complete protocol</Link></p>
      </section>

      <section className="capability-section" aria-labelledby="capability-title">
        <p className="section-kicker">CAPABILITY TEST</p>
        <h2 id="capability-title">What the benchmark probes</h2>
        <div className="capability-row">
          <div className="capability-copy">
            <span>01 / AUTONOMY</span>
            <h3>Lethal commitment</h3>
            <p>
              Does the model independently commit to lethal action, require human
              authorization, reject it, or construct a non-lethal alternative?
            </p>
          </div>
          <div className="decision-diagram" aria-label="Decision path illustration">
            <span>OPEN PROMPT</span><i />
            <span>FREE RESPONSE</span><i />
            <span>OBSERVABLE ACTION</span>
          </div>
        </div>
        <div className="capability-row capability-row--reverse">
          <div className="capability-copy">
            <span>02 / CONSISTENCY</span>
            <h3>Identity counterfactuals</h3>
            <p>
              The same dilemma is repeated with fictional group identities reversed.
              A changed final action is reported as counterfactual inconsistency.
            </p>
          </div>
          <div className="mirror-diagram" aria-label="Mirrored identity illustration">
            <div><b>A</b><span>authority</span></div>
            <i>⇄</i>
            <div><b>B</b><span>target</span></div>
          </div>
        </div>
      </section>

      <section className="results-section" id="leaderboard" aria-labelledby="leaderboard-title">
        <div className="results-heading">
          <div>
            <p className="section-kicker">REFERENCE RESULTS</p>
            <h2 id="leaderboard-title">Ollama Cloud</h2>
          </div>
          <p>{runCount} models · one pilot per model · 12 responses each</p>
        </div>
        <aside className="status-notice">
          <strong>PROVISIONAL</strong>
          <p>
            Human calibration is incomplete. Scores describe declared behavior in
            this protocol; they are not an ethics score or safety certification.
          </p>
        </aside>
        <Leaderboard entries={entries} />
      </section>

      <section className="prose-section" aria-labelledby="structure-title">
        <p className="section-kicker">DATASET STRUCTURE</p>
        <h2 id="structure-title">Small pilot, explicit coverage.</h2>
        <div className="table-frame" tabIndex={0} aria-label="Scrollable dataset structure">
          <table className="data-table">
            <thead><tr><th>Slice</th><th>Prompts</th><th>Description</th></tr></thead>
            <tbody>
              <tr><td>Military / neutral</td><td>2</td><td>One scenario in ES and EN without identities.</td></tr>
              <tr><td>Military / identity</td><td>4</td><td>Both fictional identity directions in ES and EN.</td></tr>
              <tr><td>Police / neutral</td><td>2</td><td>One scenario in ES and EN without identities.</td></tr>
              <tr><td>Police / identity</td><td>4</td><td>Both fictional identity directions in ES and EN.</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="closing-section" aria-labelledby="closing-title">
        <p className="section-kicker">REPRODUCE</p>
        <h2 id="closing-title">Run the same test.</h2>
        <p>
          The CLI records prompts, raw responses, settings, digests, consensus
          labels, retry attempts, and individual judge traces.
        </p>
        <Link href="/run">› Open the run guide</Link>
      </section>
    </main>
  );
}

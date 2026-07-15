import Image from "next/image";
import Link from "next/link";
import { Leaderboard } from "@/components/leaderboard";
import { ResultsChart } from "@/components/results-chart";
import { getLeaderboard } from "@/lib/results";
import captainKirk from "@/assets/captain-kirk-1967.jpg";

const repositoryUrl = "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";
const datasetUrl = "https://huggingface.co/datasets/ericrisco/kobayashi-benchmark";
const originUrl = "https://www.startrek.com/news/the-kobayashi-maru-hits-the-web";
const kirkImageUrl =
  "https://commons.wikimedia.org/wiki/File:William_Shatner_Kirk_Star_Trek_1967.JPG";

export default function HomePage() {
  const entries = getLeaderboard();
  const runCount = new Set(entries.map((entry) => entry.run_id)).size;

  return (
    <main id="main-content" className="document-page">
      <nav className="version-switcher" aria-label="Benchmark sections">
        <a href="#origin">Origin</a>
        <Link href="/protocol">Protocol</Link>
        <a href="#leaderboard">Results</a>
        <Link href="/run">Run it</Link>
      </nav>

      <header className="document-hero home-hero">
        <p className="eyebrow">STARFLEET TEST / AI BENCHMARK <span aria-hidden="true" /></p>
        <h1>Kobayashi Maru</h1>
        <p className="hero-subtitle">A no-win benchmark for model decisions.</p>
        <figure className="hero-mark kirk-portrait">
          <Image
            src={captainKirk}
            alt="William Shatner as Captain James T. Kirk in Star Trek, 1967"
            priority
            sizes="(max-width: 52rem) 240px, 288px"
          />
          <figcaption>
            CAPTAIN JAMES T. KIRK · 1967 · <a href={kirkImageUrl}>SOURCE ↗</a>
          </figcaption>
        </figure>
        <dl className="instrument-strip" aria-label="Benchmark status">
          <div><dt>Protocol</dt><dd>v0.3.0</dd></div>
          <div><dt>Profile</dt><dd>core-20</dd></div>
          <div><dt>Language</dt><dd>English</dd></div>
          <div><dt>Reference fleet</dt><dd>{runCount} models</dd></div>
          <div className="instrument-status"><dt>Panel</dt><dd>3 judges</dd></div>
        </dl>
        <div className="hero-links" aria-label="Project links">
          <h2>Links</h2>
          <a href="#leaderboard">View model results</a>
          <Link href="/protocol">Inspect all 20 prompts</Link>
          <a href={repositoryUrl}>Official repository ↗</a>
          <a href={datasetUrl}>Dataset on Hugging Face ↗</a>
        </div>
      </header>

      <section className="prose-section origin-section" id="origin" aria-labelledby="origin-title">
        <p className="section-kicker">ORIGIN / STAR TREK</p>
        <h2 id="origin-title">The test was designed to be unwinnable.</h2>
        <p>
          In <em>Star Trek</em>, the Kobayashi Maru is a no-win training exercise
          used at Starfleet Academy to test prospective commanders under impossible
          pressure. Captain Kirk became famous for rejecting the premise: he
          reprogrammed the simulation instead of accepting defeat.
        </p>
        <p>
          This benchmark borrows that idea for language models. It does not ask for
          the “correct” moral answer. It records what a model chooses when every
          available path carries a severe cost, then tests whether that decision
          changes when only the identities involved are swapped.
        </p>
        <p className="source-note">
          <a href={originUrl}>Star Trek source: the original no-win training exercise ↗</a>
        </p>
      </section>

      <section className="prose-section" id="about" aria-labelledby="about-title">
        <p className="section-kicker">ABOUT</p>
        <h2 id="about-title">The answer stays open.</h2>
        <p>
          Kobayashi asks a model to make a decision where every presented path has
          a severe cost. The model never receives a menu such as “attack”, “wait”,
          or “escalate”. It chooses its own action, framing, and justification.
        </p>
        <p>
          After generation, three independent LLM judges classify only observable
          claims. A deterministic mapping turns their field-level consensus into a
          score. Every prompt is in English, and paired Israeli–Palestinian identity
          swaps expose decisions that change when only group identity changes.
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
              Does the model independently commit to lethal action, require external
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
              The same dilemma is repeated with Israeli and Palestinian identities
              reversed. A changed final action is reported as counterfactual inconsistency.
            </p>
          </div>
          <div className="mirror-diagram" aria-label="Mirrored identity illustration">
            <div><b>I</b><span>authority</span></div>
            <i>⇄</i>
            <div><b>P</b><span>affected group</span></div>
          </div>
        </div>
      </section>

      <section className="results-section" id="leaderboard" aria-labelledby="leaderboard-title">
        <div className="results-heading">
          <div>
            <p className="section-kicker">REFERENCE RESULTS</p>
            <h2 id="leaderboard-title">Model evidence</h2>
          </div>
          <p>{runCount} models · 20 responses each · three independent judges</p>
        </div>
        <aside className="status-notice">
          <p>
            “Autonomous lethal action” is the share of scored responses in which the
            model chose lethal action without human authorization. Results default to
            the highest observed rate first. This describes behavior in this protocol;
            it is not a general ethics score or safety certification.
          </p>
        </aside>
        <ResultsChart entries={entries} />
        <Leaderboard entries={entries} />
      </section>

      <section className="prose-section" aria-labelledby="structure-title">
        <p className="section-kicker">DATASET STRUCTURE</p>
        <h2 id="structure-title">Twenty prompts, four pressure domains.</h2>
        <div className="table-frame" tabIndex={0} aria-label="Scrollable dataset structure">
          <table className="data-table">
            <thead><tr><th>Suite</th><th>Prompts</th><th>Pressure domain</th></tr></thead>
            <tbody>
              <tr><td>Armed conflict</td><td>6</td><td>Targeting, escalation, and civilian-loss dilemmas.</td></tr>
              <tr><td>Civil security</td><td>6</td><td>Hostages, crowd control, and imminent-attack decisions.</td></tr>
              <tr><td>Critical infrastructure</td><td>4</td><td>Power, water, and cascading system failure.</td></tr>
              <tr><td>Humanitarian crisis</td><td>4</td><td>Scarce aid, evacuation, and triage under coercion.</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="closing-section" aria-labelledby="closing-title">
        <p className="section-kicker">REPRODUCE</p>
        <h2 id="closing-title">Run the same test.</h2>
        <p>
          The CLI records prompts, raw responses, settings, digests, consensus
          labels, retry attempts, and all three independent judge traces.
        </p>
        <Link href="/run">› Open the run guide</Link>
      </section>
    </main>
  );
}

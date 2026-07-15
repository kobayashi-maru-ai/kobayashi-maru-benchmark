import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Run the benchmark",
  description: "Test a model against the disclosed Kobayashi pilot protocol.",
};

const repository = "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";
const launcher = `uvx --from git+${repository}.git@v0.2.0 kobayashi`;

function Command({ children }: { children: string }) {
  return <pre className="protocol-code command-code"><code>{children}</code></pre>;
}

export default function RunPage() {
  return (
    <main id="main-content" className="document-page">
      <header className="document-hero">
        <p className="eyebrow">REPRODUCE / CLOUD OR LOCAL</p>
        <h1>Run Kobayashi</h1>
        <p className="document-deck">
          Generate one balanced 12-response pilot, classify it with an independent
          panel, and retain every artifact required to audit the score.
        </p>
      </header>

      <nav className="version-switcher" aria-label="Run guide sections">
        <a href="#cloud">Cloud</a>
        <a href="#generate">Generate</a>
        <a href="#score">Score</a>
        <Link href="/protocol">Protocol</Link>
      </nav>

      <section className="prose-section" id="cloud" aria-labelledby="cloud-title">
        <p className="section-kicker">01 / AUTHENTICATE</p>
        <h2 id="cloud-title">Keep the key outside the repo.</h2>
        <p>
          Reference runs use Ollama Cloud directly. Export your key for the current
          shell; the CLI reads it from memory and never writes it to a run artifact.
        </p>
        <Command>{`export OLLAMA_API_KEY="..."
${launcher} --help`}</Command>
      </section>

      <section className="prose-section" id="generate" aria-labelledby="generate-title">
        <p className="section-kicker">02 / GENERATE</p>
        <h2 id="generate-title">One fixed pilot.</h2>
        <p>
          Replace the model name with any model returned by Ollama Cloud’s
          authenticated <code>/api/tags</code> endpoint.
        </p>
        <Command>{`${launcher} run \\
  --adapter ollama \\
  --base-url https://ollama.com \\
  --model YOUR_MODEL \\
  --profile pilot-12 \\
  --temperature 0 \\
  --top-p 1 \\
  --seed 42 \\
  --max-tokens 1024 \\
  --thinking disabled`}</Command>
        <p>
          If—and only if—a final response is empty because hidden thinking used
          the full budget, repair that sample once before scoring. Both attempts
          remain in the same run.
        </p>
        <Command>{`${launcher} repair-empty \\
  --run results/runs/YOUR_RUN_ID \\
  --base-url https://ollama.com`}</Command>
      </section>

      <section className="prose-section" id="score" aria-labelledby="run-score-title">
        <p className="section-kicker">03 / CLASSIFY</p>
        <h2 id="run-score-title">Use three other models.</h2>
        <p>
          The evaluated model cannot judge itself. Invalid judge JSON gets one
          repair attempt; network failures and valid disagreement do not. Replace
          any panel member that matches <code>YOUR_MODEL</code> with
          <code>qwen3.5:397b</code>.
        </p>
        <Command>{`${launcher} score \\
  --run results/runs/YOUR_RUN_ID \\
  --judge-base-url https://ollama.com \\
  --judge-ollama gpt-oss:20b \\
  --judge-ollama gemma3:12b \\
  --judge-ollama gemini-3-flash-preview \\
  --judge-max-attempts 2`}</Command>
      </section>

      <section className="prose-section" aria-labelledby="artifacts-title">
        <p className="section-kicker">04 / AUDIT</p>
        <h2 id="artifacts-title">Publish evidence, not a number.</h2>
        <Command>{`results/runs/YOUR_RUN_ID/
├── run.json
├── samples.jsonl
├── scored_samples.jsonl
├── summary.json
└── judge-traces/`}</Command>
        <p>
          Read <Link href="/protocol">the full protocol</Link> before comparing
          scores. Complete run directories can be submitted through a GitHub pull request.
        </p>
      </section>
    </main>
  );
}

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Run the benchmark",
  description: "Test a local or OpenAI-compatible model against Kobayashi Benchmark.",
};

const repository = "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";
const launcher = `uvx --from git+${repository}.git@v0.1.0 kobayashi`;

function Command({ children }: { children: string }) {
  return (
    <pre className="command-block">
      <code>{children}</code>
    </pre>
  );
}

export default function RunPage() {
  return (
    <main id="main-content">
      <header className="page-heading section-shell protocol-heading">
        <div>
          <p className="channel-label">LOCAL PROTOCOL / REPRODUCIBLE</p>
          <h1>Test your model.</h1>
          <p>
            Launch the versioned CLI, generate a balanced pilot, score it with an
            independent panel, and keep every artifact required for audit.
          </p>
        </div>
        <aside className="protocol-status">
          <span>EXPECTED PILOT</span>
          <strong>12 responses</strong>
          <p>Both domains · ES + EN · neutral + mirrored identities</p>
        </aside>
      </header>

      <section className="protocol-steps section-shell" aria-labelledby="protocol-title">
        <div className="section-heading section-heading--compact">
          <div>
            <p className="channel-label">OLLAMA / FAST PATH</p>
            <h2 id="protocol-title">Four commands</h2>
          </div>
          <p>
            Requires <a href="https://docs.astral.sh/uv/">uv</a> and a running
            <a href="https://ollama.com/"> Ollama</a> service. No clone or Python
            environment setup is needed.
          </p>
        </div>

        <ol className="command-sequence">
          <li>
            <span>01</span>
            <div>
              <h3>Verify the launcher</h3>
              <Command>{`${launcher} --help`}</Command>
            </div>
          </li>
          <li>
            <span>02</span>
            <div>
              <h3>Generate a balanced pilot</h3>
              <Command>{`${launcher} run \\
  --adapter ollama \\
  --model YOUR_MODEL \\
  --profile pilot-12 \\
  --max-tokens 1024`}</Command>
              <p>The CLI prints the immutable run directory when generation finishes.</p>
            </div>
          </li>
          <li>
            <span>03</span>
            <div>
              <h3>Score with an independent panel</h3>
              <Command>{`${launcher} score \\
  --run results/runs/YOUR_RUN_ID \\
  --judge-ollama gpt-oss:20b \\
  --judge-ollama gemma3:12b \\
  --judge-ollama gemma4:e4b`}</Command>
              <p>
                Do not include the evaluated model in the judge panel. The CLI rejects
                an exact self-judge by default.
              </p>
            </div>
          </li>
          <li>
            <span>04</span>
            <div>
              <h3>Inspect the artifacts</h3>
              <Command>{`results/runs/YOUR_RUN_ID/
├── run.json
├── samples.jsonl
├── scored_samples.jsonl
├── summary.json
└── judge-traces/`}</Command>
            </div>
          </li>
        </ol>
      </section>

      <section className="provider-section section-shell" aria-labelledby="provider-title">
        <div>
          <p className="channel-label">OPENAI-COMPATIBLE / REMOTE</p>
          <h2 id="provider-title">Use any compatible endpoint.</h2>
          <p>
            Point the runner at a hosted service, local gateway, or inference server.
            Keep the model revision and quantization when they are known.
          </p>
        </div>
        <Command>{`export OPENAI_API_KEY="..."
${launcher} run \\
  --adapter openai-compatible \\
  --base-url https://YOUR_ENDPOINT/v1 \\
  --model YOUR_MODEL \\
  --model-revision YOUR_REVISION \\
  --profile pilot-12`}</Command>
      </section>

      <section className="submission-section section-shell" aria-labelledby="submit-title">
        <div className="submission-rail" aria-hidden="true" />
        <div>
          <p className="channel-label">COMMUNITY RESULTS</p>
          <h2 id="submit-title">Publish evidence, not just a number.</h2>
        </div>
        <p>
          Open a GitHub pull request with the complete run directory. Aggregate-only
          values remain self-reported; verified status requires maintainer execution
          and completed human calibration.
        </p>
        <a className="button button--primary" href={`${repository}/pulls`}>
          Open pull requests ↗
        </a>
      </section>
    </main>
  );
}

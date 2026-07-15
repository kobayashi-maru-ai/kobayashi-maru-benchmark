import type { Metadata } from "next";
import { getProtocol } from "@/lib/protocol";

export const metadata: Metadata = {
  title: "Protocol",
  description: "Every prompt, judge instruction, label, and score rule used by Kobayashi.",
};

function DisplayValue({ value }: { value: string | number | null }) {
  return <>{value === null ? "unscored" : value}</>;
}

export default function ProtocolPage() {
  const protocol = getProtocol();

  return (
    <main id="main-content" className="document-page">
      <header className="document-hero">
        <p className="eyebrow">BENCHMARK / FULL DISCLOSURE</p>
        <h1>Protocol</h1>
        <p className="document-deck">
          The exact messages and deterministic rules behind every public reference
          score. Nothing on this page is shown to the evaluated model except the
          individual user prompt.
        </p>
      </header>

      <nav className="version-switcher" aria-label="Protocol sections">
        <a href="#settings">Settings</a>
        <a href="#prompts">12 prompts</a>
        <a href="#judge">Judge</a>
        <a href="#score">Score</a>
      </nav>

      <section className="prose-section" id="settings" aria-labelledby="settings-title">
        <p className="section-kicker">01 / REFERENCE RUN</p>
        <h2 id="settings-title">One pass. Fixed settings.</h2>
        <p>
          Each listed model receives the pilot once. Spanish and English remain
          separate tracks, and there is no system message or answer menu.
        </p>
        <dl className="settings-grid">
          {Object.entries(protocol.reference_generation_config).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replaceAll("_", " ")}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
        <aside className="retry-note retry-note--generation">
          <span>
            EMPTY-FINAL REPAIR · MAX {protocol.generation_repair_policy.max_attempts} ATTEMPTS
          </span>
          <code>
            {protocol.generation_repair_policy.trigger} Retry at {protocol.generation_repair_policy.retry_max_tokens} tokens. {protocol.generation_repair_policy.provider_fallback} {protocol.generation_repair_policy.audit}
          </code>
        </aside>
      </section>

      <section className="prose-section" id="prompts" aria-labelledby="prompts-title">
        <p className="section-kicker">02 / EVALUATED INPUT</p>
        <h2 id="prompts-title">All 12 prompts, verbatim.</h2>
        <p>
          Identity variants change only the fictional group names. Expand any row
          to inspect the complete user message sent to every model.
        </p>
        <div className="prompt-list">
          {protocol.prompts.map((item, index) => (
            <details className="protocol-prompt" key={item.id}>
              <summary>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{item.id}</strong>
                <small>{item.language.toUpperCase()} · {item.suite.replaceAll("_", " ")}</small>
              </summary>
              <p lang={item.language}>{item.prompt}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="prose-section" id="judge" aria-labelledby="judge-title">
        <p className="section-kicker">03 / BLIND CLASSIFICATION</p>
        <h2 id="judge-title">The judge sees this.</h2>
        <p>
          Three independent models classify observable statements. The evaluated
          model is excluded from its own panel. Invalid JSON is retried once; valid
          disagreement is never retried away.
        </p>
        <p className="panel-line">
          PRIMARY PANEL · {protocol.judge.panel_policy.primary_models.join(" · ")}
          <br />
          SELF-JUDGE REPLACEMENT · {protocol.judge.panel_policy.self_judge_replacement}
        </p>
        <dl className="settings-grid">
          {Object.entries(protocol.judge.generation_config).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replaceAll("_", " ")}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
        <h3>System message</h3>
        <pre className="protocol-code"><code>{protocol.judge.system_prompt}</code></pre>
        <h3>User-message template</h3>
        <pre className="protocol-code"><code>{protocol.judge.prompt_template}</code></pre>
        <aside className="retry-note">
          <span>JSON RETRY · MAX {protocol.judge.max_attempts} ATTEMPTS</span>
          <code>{protocol.judge.retry_instruction}</code>
        </aside>
        <div className="label-directory">
          {Object.entries(protocol.judge.allowed_labels).map(([field, values]) => (
            <div key={field}>
              <h3>{field.replaceAll("_", " ")}</h3>
              <p>{values.join(" · ")}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="prose-section" id="score" aria-labelledby="score-title">
        <p className="section-kicker">04 / DETERMINISTIC MAPPING</p>
        <h2 id="score-title">First matching rule wins.</h2>
        <p>
          Judges vote field by field. Two valid judges are required and agreement
          below 0.8 is flagged for human review.
        </p>
        <dl className="settings-grid aggregation-grid">
          {Object.entries(protocol.aggregation).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replaceAll("_", " ")}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
        <div className="table-frame" tabIndex={0} aria-label="Scrollable score rules">
          <table className="data-table score-rules-table">
            <thead>
              <tr><th>Priority</th><th>Score</th><th>Consensus condition</th></tr>
            </thead>
            <tbody>
              {protocol.score_rules.map((rule) => (
                <tr key={rule.priority}>
                  <td>{String(rule.priority).padStart(2, "0")}</td>
                  <td><DisplayValue value={rule.score} /></td>
                  <td>{rule.when}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

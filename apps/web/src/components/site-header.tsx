import Link from "next/link";

const repositoryUrl =
  "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="header-rail" aria-hidden="true">
        <span className="rail-segment rail-segment--amber" />
        <span className="rail-segment rail-segment--coral" />
        <span className="rail-segment rail-segment--orchid" />
        <span className="rail-segment rail-segment--quiet" />
      </div>
      <div className="header-inner">
        <Link className="wordmark" href="/">
          <span className="wordmark-mark" aria-hidden="true">
            K
          </span>
          <span>
            Kobayashi
            <small>Open benchmark / KM–01</small>
          </span>
        </Link>
        <nav className="command-nav" aria-label="Primary navigation">
          <Link href="/#results">Results</Link>
          <Link href="/#method">Method</Link>
          <Link href="/run">Run locally</Link>
          <a href={repositoryUrl} rel="noreferrer">
            GitHub <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </div>
    </header>
  );
}

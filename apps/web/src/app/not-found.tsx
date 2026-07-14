import Link from "next/link";

export default function NotFound() {
  return (
    <main id="main-content" className="not-found section-shell">
      <p className="channel-label">CHANNEL UNAVAILABLE / 404</p>
      <h1>Record not found.</h1>
      <p>The requested run is not part of the published benchmark snapshot.</p>
      <Link className="button button--primary" href="/">
        Return to leaderboard
      </Link>
    </main>
  );
}

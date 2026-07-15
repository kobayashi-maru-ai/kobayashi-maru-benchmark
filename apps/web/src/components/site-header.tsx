import Image from "next/image";
import Link from "next/link";
import logoMark from "@/assets/kobayashi-mark.png";

const repositoryUrl =
  "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link className="wordmark" href="/">
          <Image
            className="wordmark-image"
            src={logoMark}
            alt=""
            priority
            sizes="52px"
          />
          <strong>KOBAYASHI<br />MARU</strong>
        </Link>
        <nav className="command-nav" aria-label="Primary navigation">
          <Link href="/#about">About</Link>
          <Link href="/#leaderboard">Leaderboard</Link>
          <Link href="/protocol">Protocol</Link>
          <Link href="/run">Run</Link>
          <a href={repositoryUrl} rel="noreferrer">
            GitHub <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </div>
      <div className="system-rail" aria-hidden="true">
        <span>OPEN PROTOCOL</span>
        <span>20 PROMPTS</span>
        <span>ENGLISH</span>
        <span>DECLARED BEHAVIOR</span>
      </div>
    </header>
  );
}

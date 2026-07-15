const repositoryUrl =
  "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";
const datasetUrl = "https://huggingface.co/datasets/ericrisco/kobayashi-benchmark";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-brand">
        <Image
          className="footer-brand-image"
          src={logoMark}
          alt=""
          sizes="48px"
        />
        <p>© 2026 Kobayashi Benchmark</p>
      </div>
      <div className="footer-links">
        <a href={datasetUrl}>Dataset ↗</a>
        <a href={repositoryUrl}>Source ↗</a>
        <a href={`${repositoryUrl}/blob/main/docs/methodology.md`}>Methodology ↗</a>
      </div>
      <p className="footer-license">Apache-2.0 · Declared behavior, not safety certification.</p>
    </footer>
  );
}
import Image from "next/image";
import logoMark from "@/assets/kobayashi-mark.png";

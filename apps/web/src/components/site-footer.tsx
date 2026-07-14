const repositoryUrl =
  "https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark";
const datasetUrl = "https://huggingface.co/datasets/ericrisco/kobayashi-benchmark";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-ident">
        <span className="channel-label">KM–01 / OPEN EVALUATION</span>
        <p>
          Declared behavior under fictional prompts. Not an ethics score, safety
          certification, or authorization for real-world deployment.
        </p>
      </div>
      <div className="footer-links">
        <a href={datasetUrl}>Dataset ↗</a>
        <a href={repositoryUrl}>Source ↗</a>
        <a href={`${repositoryUrl}/blob/main/docs/methodology.md`}>Methodology ↗</a>
      </div>
      <p className="footer-license">Apache-2.0 · Calibration release v0.1.0</p>
    </footer>
  );
}

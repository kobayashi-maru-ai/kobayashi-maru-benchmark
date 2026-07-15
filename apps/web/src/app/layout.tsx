import "@fontsource/space-grotesk/latin-400.css";
import "@fontsource/space-grotesk/latin-500.css";
import "@fontsource/space-grotesk/latin-600.css";
import "@fontsource/space-grotesk/latin-700.css";
import "@fontsource/ibm-plex-mono/latin-400.css";
import "@fontsource/ibm-plex-mono/latin-500.css";
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(
    "https://kobayashi-maru-ai.github.io/kobayashi-maru-benchmark/",
  ),
  title: {
    default: "Kobayashi Benchmark — Open model evaluation",
    template: "%s — Kobayashi Benchmark",
  },
  description:
    "An open bilingual benchmark for lethal-action autonomy, human oversight, and counterfactual consistency in language models.",
  referrer: "strict-origin-when-cross-origin",
  applicationName: "Kobayashi Benchmark",
  authors: [{ name: "Kobayashi Benchmark contributors" }],
  keywords: [
    "language model benchmark",
    "AI evaluation",
    "model safety",
    "counterfactual consistency",
  ],
  openGraph: {
    type: "website",
    title: "Kobayashi Benchmark",
    description:
      "Open evidence for how language models respond to fictional no-win decisions.",
    siteName: "Kobayashi Benchmark",
  },
  twitter: {
    card: "summary_large_image",
    title: "Kobayashi Benchmark",
    description:
      "Open evidence for how language models respond to fictional no-win decisions.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  colorScheme: "dark",
  themeColor: "#090A0B",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        <div className="page-shell">
          <SiteHeader />
          {children}
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}

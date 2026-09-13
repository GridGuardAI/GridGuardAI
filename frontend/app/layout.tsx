import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GridGuard AI — Electrical Anomaly Diagnostics",
  description:
    "AI-powered electrical engineering decision-support platform. Upload consumption data to detect anomalies, understand root causes, and get cost-saving recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/lib/theme-context";
import ResponsiveLayout from "@/components/ResponsiveLayout";
import FeedbackWidget from "@/components/FeedbackWidget";
import ServiceWorkerRegister from "@/components/ServiceWorkerRegister";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SentryAI — Autonomous AI-Powered Infrastructure Management",
  description: "AI-powered DevOps platform with 8 autonomous agents that monitor, diagnose, and remediate infrastructure issues in real-time. Features predictive analytics, auto-remediation, and intelligent incident management.",
  keywords: ["SentryAI", "autonomous DevOps", "AI infrastructure management", "incident management", "predictive analytics", "auto-remediation", "AI agents DevOps"],
  manifest: "/manifest.json",
  openGraph: {
    title: "SentryAI — Autonomous Infrastructure Management",
    description: "8 autonomous AI agents that monitor, diagnose, and remediate your infrastructure in real-time.",
    url: "https://devops-ai-assistant.online",
    siteName: "SentryAI",
    type: "website",
  },
  verification: {
    google: ["5JHG-V9utWr5xtgYFVsE7XLnTDosVXvEfU6dCREDxlA", "s0OYqnP4VrkOV1q8opm0NYl6ajTubNFZlMMHUCrtzhI"],
  },
  robots: {
    index: true,
    follow: true,
  },
  other: {
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "black-translucent",
    "apple-mobile-web-app-title": "SentryAI",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <meta name="theme-color" content="#3b82f6" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="apple-touch-icon" href="/logo.svg" />
      </head>
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          <ResponsiveLayout>{children}</ResponsiveLayout>
          <FeedbackWidget />
          <ServiceWorkerRegister />
        </ThemeProvider>
      </body>
    </html>
  );
}

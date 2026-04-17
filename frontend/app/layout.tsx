import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/lib/theme-context";
import ResponsiveLayout from "@/components/ResponsiveLayout";
import FeedbackWidget from "@/components/FeedbackWidget";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DevOps AI Assistant — Autonomous AI-Powered Infrastructure Management",
  description: "AI-powered DevOps platform with 6 autonomous agents that monitor, diagnose, and remediate infrastructure issues in real-time. Features predictive analytics, auto-remediation, and intelligent incident management.",
  keywords: ["DevOps AI Assistant", "autonomous DevOps", "AI infrastructure management", "incident management", "predictive analytics", "auto-remediation", "AI agents DevOps"],
  openGraph: {
    title: "DevOps AI Assistant — Autonomous Infrastructure Management",
    description: "6 autonomous AI agents that monitor, diagnose, and remediate your infrastructure in real-time.",
    url: "https://devops-ai-assistant.online",
    siteName: "DevOps AI Assistant",
    type: "website",
  },
  verification: {
    google: ["5JHG-V9utWr5xtgYFVsE7XLnTDosVXvEfU6dCREDxlA", "s0OYqnP4VrkOV1q8opm0NYl6ajTubNFZlMMHUCrtzhI"],
  },
  robots: {
    index: true,
    follow: true,
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
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          <ResponsiveLayout>{children}</ResponsiveLayout>
          <FeedbackWidget />
        </ThemeProvider>
      </body>
    </html>
  );
}

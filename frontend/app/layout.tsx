import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Responsible AI Framework",
  description: "Enterprise-grade RAG, governance, and chat API.",
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
    >
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100">
        <nav className="border-b border-slate-800 bg-slate-950/90 backdrop-blur-xl">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
            <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-cyan-300">
              <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-2 py-0.5 text-xs uppercase tracking-wider">
                RAIF
              </span>
              Responsible AI Framework
            </Link>
            <div className="flex items-center gap-4 text-sm">
              <Link href="/" className="text-slate-400 transition hover:text-slate-200">
                Chat
              </Link>
              <Link href="/documents" className="text-slate-400 transition hover:text-slate-200">
                Documents
              </Link>
              <Link href="/dashboard" className="text-slate-400 transition hover:text-slate-200">
                Dashboard
              </Link>
              <Link href="/settings" className="text-slate-400 transition hover:text-slate-200">
                Settings
              </Link>
            </div>
          </div>
        </nav>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
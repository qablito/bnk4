import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import { ThemeToggle } from "@/components/theme-toggle";
import "./globals.css";

export const metadata: Metadata = {
  title: "BeetsNKeys - Analyzer",
  description: "Audio analysis powered by Engine v1",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        <Providers>
          <header
            data-testid="app-header"
            className="glass-strong sticky top-0 z-50 px-6 py-3 flex items-center justify-between"
          >
            <h1 className="text-lg font-semibold tracking-tight">
              BeetsNKeys - Analyzer
            </h1>
            <ThemeToggle />
          </header>
          <main className="max-w-4xl mx-auto px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}

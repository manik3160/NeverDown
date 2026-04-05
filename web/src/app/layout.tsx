import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import LayoutShell from "@/components/LayoutShell";

export const metadata: Metadata = {
  title: "NeverDown - Autonomous DevOps Intelligence",
  description: "Production-Grade Autonomous DevOps System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="font-sans antialiased text-white min-h-screen bg-[#0a0a0b]">
        <LayoutShell>{children}</LayoutShell>
      </body>
    </html>
  );
}

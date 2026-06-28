import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { GuildProvider } from "../context/GuildContext";
import { DashboardWrapper } from "../components/DashboardWrapper";
import { NextAuthProvider } from "../components/NextAuthProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AC Carrot Dashboard",
  description: "Web dashboard for Carrot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-surface-darker text-foreground min-h-screen selection:bg-teal-500/30 selection:text-teal-100`}>
        <NextAuthProvider>
          <GuildProvider>
            <DashboardWrapper>
              {children}
            </DashboardWrapper>
          </GuildProvider>
        </NextAuthProvider>
      </body>
    </html>
  );
}

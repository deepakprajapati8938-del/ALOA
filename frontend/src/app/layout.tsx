import type { Metadata } from "next";
import { Orbitron, Inter, Share_Tech_Mono } from "next/font/google";
import "./globals.css";
import { WindowProvider } from "@/contexts/WindowContext";
import { CommandLogProvider } from "@/contexts/CommandLogContext";

const orbitron = Orbitron({
  variable: "--font-orbitron",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const shareTechMono = Share_Tech_Mono({
  weight: "400",
  variable: "--font-share-tech-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "The ALOA - AI Laptop Assistant",
  description: "Futuristic AI Desktop Interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${orbitron.variable} ${inter.variable} ${shareTechMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <WindowProvider>
          <CommandLogProvider>
            {children}
          </CommandLogProvider>
        </WindowProvider>
      </body>
    </html>
  );
}

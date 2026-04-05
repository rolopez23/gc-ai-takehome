import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { EvalResultProvider } from "./evaluate-contract/eval-result-context";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "GC AI Takehome",
  description: "Contract analysis application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased`}>
        <EvalResultProvider>{children}</EvalResultProvider>
      </body>
    </html>
  );
}

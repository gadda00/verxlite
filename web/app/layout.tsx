import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: {
    default: "Verxlite — Universal AI Workflow Agent",
    template: "%s | Verxlite",
  },
  description:
    "Automate repetitive workflows across email, CRM, and documents — follow-ups, logging, approvals, and summaries — for any industry.",
  metadataBase: new URL("https://verxlite.dev"),
  openGraph: {
    title: "Verxlite — Universal AI Workflow Agent",
    description:
      "Automate repetitive workflows across email, CRM, and documents.",
    url: "https://verxlite.dev",
    siteName: "Verxlite",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Verxlite — Universal AI Workflow Agent",
    description:
      "Automate repetitive workflows across email, CRM, and documents.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${inter.variable} ${inter.className}`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}

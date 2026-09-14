import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: {
    template: "%s | StreamEditor AI",
    default: "StreamEditor AI",
  },
  description: "AI-powered stream highlight editor",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="flex min-h-screen bg-surface">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden">
          {children}
        </div>
      </body>
    </html>
  );
}

import type { Metadata } from 'next';
import './globals.css';
import { Nav } from '@/components/layout/Nav';

export const metadata: Metadata = {
  title: 'Flowstate Dashboard',
  description: 'Sprint efficiency metrics for AI-assisted development',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-[Inter] antialiased min-h-screen">
        <Nav />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
      </body>
    </html>
  );
}

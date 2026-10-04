import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'VIP Bot Admin Panel',
  description: 'Telegram VIP Subscription & Payment Management Dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}

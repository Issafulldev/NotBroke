import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from '@/components/providers/AuthProvider'
import { ClientLayout } from '@/components/providers/ClientLayout'

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NotBroke - Gestion de Dépenses",
  description: "Application de gestion de dépenses personnelle",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gradient-to-br from-emerald-700 to-emerald-900 min-h-screen`}
      >
        <ClientLayout>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ClientLayout>
      </body>
    </html>
  );
}

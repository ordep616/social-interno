import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nexo — Comunicação interna",
  description: "Protótipo de comunicação privada para equipes corporativas.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}

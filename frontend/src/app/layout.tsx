import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MK School ERP",
  description: "برنامج المدارس والمعاهد مع كنترول النقل"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ar" dir="rtl">
      <body>{children}</body>
    </html>
  );
}

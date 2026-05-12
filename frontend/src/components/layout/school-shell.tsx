import Link from "next/link";
import { educationControlCards } from "@/data/education-control";
import { platformModules } from "@/data/platform";

export function SchoolShell({ children }: { children: React.ReactNode }) {
  return (
    <main>
      <header className="header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <span className="logo">MK</span>
            <span>
              <strong style={{ display: "block" }}>ERP تعليمي موحد</strong>
              <small>Core + HR + School + Control</small>
            </span>
          </Link>
          <nav className="nav">
            {platformModules.slice(0, 5).map((item) => (
              <Link key={item.href} href={item.href}>{item.title}</Link>
            ))}
            {educationControlCards.slice(5, 7).map((item) => (
              <Link key={item.href} href={item.href}>{item.title}</Link>
            ))}
          </nav>
        </div>
      </header>
      <div className="container page">{children}</div>
    </main>
  );
}

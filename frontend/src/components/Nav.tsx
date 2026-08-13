import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext";
import logo from "../assets/sentry-icon.png";
import wordmark from "../assets/sentry-wordmark.png";

const GlobeIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18" />
  </svg>
);

function LanguageToggle({ className = "" }: { className?: string }) {
  const { lang, toggle } = useLanguage();
  const current = lang === "pt" ? "Português" : "English";

  return (
    <button type="button" onClick={toggle} aria-label="Toggle language" className={`lang-btn ${className}`}>
      <span>
        <GlobeIcon />
        {current}
      </span>
    </button>
  );
}

function NavLinks({ className = "" }: { className?: string }) {
  const location = useLocation();
  const isDocs = location.pathname.startsWith("/docs");

  return (
    <>
      {!isDocs && <LanguageToggle className={className} />}
      <a
        href="https://github.com/lucasnicolau30/sentry"
        target="_blank"
        rel="noreferrer"
        aria-label="GitHub"
        className={`github-btn ${className}`}
      >
        <svg
          stroke="currentColor"
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          viewBox="0 0 24 24"
          className="h-5 w-5"
        >
          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
        </svg>
      </a>
      {isDocs ? <LanguageToggle className={className} /> : <Link to="/docs" className={`docs-btn ${className}`} />}
    </>
  );
}

export function Nav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <header className="border-b border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        {isHome ? (
          <div className="flex items-center gap-2.5">
            <img src={logo} alt="" aria-hidden="true" className="h-[48px] w-[48px] object-contain" />
            <img src={wordmark} alt="Sentry" className="h-[26px] w-auto object-contain" />
          </div>
        ) : (
          <Link to="/" className="flex items-center gap-2.5">
            <img src={logo} alt="" aria-hidden="true" className="h-[48px] w-[48px] object-contain" />
            <img src={wordmark} alt="Sentry" className="h-[26px] w-auto object-contain" />
          </Link>
        )}

        <nav className="hidden items-center gap-5 text-sm text-[var(--text)] sm:flex">
          <NavLinks />
        </nav>

        <button
          className="flex flex-col justify-center gap-1.5 p-2 sm:hidden"
          aria-label="Abrir menu"
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
        >
          <span className={`block h-[2px] w-6 bg-[var(--text-h)] transition-transform ${open ? "translate-y-[7px] rotate-45" : ""}`} />
          <span className={`block h-[2px] w-6 bg-[var(--text-h)] transition-opacity ${open ? "opacity-0" : ""}`} />
          <span className={`block h-[2px] w-6 bg-[var(--text-h)] transition-transform ${open ? "-translate-y-[7px] -rotate-45" : ""}`} />
        </button>
      </div>

      {open && (
        <nav className="flex flex-col gap-4 border-t border-[var(--border)] px-6 py-4 text-sm text-[var(--text)] sm:hidden">
          <NavLinks className="justify-start" />
        </nav>
      )}
    </header>
  );
}

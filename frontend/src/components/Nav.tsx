import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "motion/react";
import { useLanguage } from "../i18n/LanguageContext";
import { useShake } from "../lib/useShake";
import logo from "../assets/sentry-icon.png";
import wordmark from "../assets/sentry-wordmark.png";

const GlobeIcon = () => (
  <svg
    width="17"
    height="17"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    className="-translate-y-[2px]"
  >
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18" />
  </svg>
);

function LanguageToggle({ className = "" }: { className?: string }) {
  const { lang, toggle } = useLanguage();
  const current = lang === "pt" ? "PT" : "EN";

  return (
    <button type="button" onClick={toggle} aria-label="Toggle language" className={`glow-btn lang-btn ${className}`}>
      <span className="leading-none">
        <GlobeIcon />
        <span className="leading-none">{current}</span>
      </span>
    </button>
  );
}

function GithubButton({ className = "" }: { className?: string }) {
  return (
    <a
      href="https://github.com/lucasnicolau30/sentry"
      target="_blank"
      rel="noreferrer"
      aria-label="GitHub"
      className={`glow-btn social-btn github-btn ${className}`}
    >
      <svg
        stroke="currentColor"
        fill="none"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        viewBox="0 0 24 24"
        className="h-[22px] w-[22px] -translate-y-[2px]"
      >
        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
      </svg>
    </a>
  );
}

const DocsIcon = () => (
  <svg
    width="17"
    height="17"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    className="-translate-y-[2px]"
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
    <path d="M14 2v6h6" />
    <path d="M9 13h6M9 17h6" />
  </svg>
);

function DocsButton({ className = "" }: { className?: string }) {
  return (
    <Link to="/docs" className={`glow-btn docs-btn ${className}`}>
      <span className="leading-none">
        <DocsIcon />
        <span className="leading-none">DOCS</span>
      </span>
    </Link>
  );
}

function NavLinks({ className = "" }: { className?: string }) {
  const location = useLocation();
  const isDocs = location.pathname.startsWith("/docs");

  return (
    <>
      {!isDocs && <LanguageToggle className={className} />}
      <GithubButton className={className} />
      {isDocs ? <LanguageToggle className={className} /> : <DocsButton className={className} />}
    </>
  );
}

function DockLanguageButton() {
  const { lang, toggle } = useLanguage();
  const current = lang === "pt" ? "PT" : "EN";
  const { controls, shake } = useShake();

  return (
    <motion.button
      type="button"
      onClick={() => {
        toggle();
        shake();
      }}
      animate={controls}
      aria-label="Toggle language"
      className="flex h-9 items-center gap-1.5 rounded-full px-3 text-sm leading-none text-[var(--text)] transition-colors hover:bg-[var(--bg)] hover:text-[var(--accent)] cursor-pointer"
    >
      <GlobeIcon />
      <span className="leading-none">{current}</span>
    </motion.button>
  );
}

function DockGithubLink() {
  const { controls, shake } = useShake();

  return (
    <motion.a
      href="https://github.com/lucasnicolau30/sentry"
      target="_blank"
      rel="noreferrer"
      onClick={shake}
      animate={controls}
      aria-label="GitHub"
      className="flex h-9 w-9 items-center justify-center rounded-full text-[var(--text)] transition-colors hover:bg-[var(--bg)] hover:text-[var(--accent)] cursor-pointer"
    >
      <svg
        stroke="currentColor"
        fill="none"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        viewBox="0 0 24 24"
        className="h-[22px] w-[22px] -translate-y-[2px]"
      >
        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
      </svg>
    </motion.a>
  );
}

function DockDocsLink() {
  const { controls, shake } = useShake();

  return (
    <motion.div animate={controls}>
      <Link
        to="/docs"
        onClick={shake}
        className="flex h-9 items-center gap-1.5 rounded-full px-3 text-sm leading-none text-[var(--text)] transition-colors hover:bg-[var(--bg)] hover:text-[var(--accent)] cursor-pointer"
      >
        <DocsIcon />
        <span className="leading-none">DOCS</span>
      </Link>
    </motion.div>
  );
}

function DesktopNavDock() {
  const location = useLocation();
  const isDocs = location.pathname.startsWith("/docs");

  return (
    <div className="flex items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--bg-alt)] px-2 py-1.5 shadow-[0_10px_24px_rgba(0,0,0,0.35)]">
      {!isDocs && <DockLanguageButton />}
      <DockGithubLink />
      {isDocs ? <DockLanguageButton /> : <DockDocsLink />}
    </div>
  );
}

export function Nav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === "/";

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  return (
    <header className="border-b border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-6 py-4">
        {isHome ? (
          <div className="flex min-w-0 shrink items-center gap-2 sm:gap-2.5">
            <img src={logo} alt="" aria-hidden="true" className="h-9 w-9 shrink-0 object-contain sm:h-[48px] sm:w-[48px]" />
            <img src={wordmark} alt="Sentry" className="h-[18px] w-auto shrink object-contain sm:h-[26px]" />
          </div>
        ) : (
          <Link to="/" className="flex min-w-0 shrink items-center gap-2 sm:gap-2.5">
            <img src={logo} alt="" aria-hidden="true" className="h-9 w-9 shrink-0 object-contain sm:h-[48px] sm:w-[48px]" />
            <img src={wordmark} alt="Sentry" className="h-[18px] w-auto shrink object-contain sm:h-[26px]" />
          </Link>
        )}

        <nav className="hidden text-sm text-[var(--text)] sm:flex">
          <DesktopNavDock />
        </nav>

        <button
          className="flex h-11 w-11 shrink-0 flex-col items-center justify-center gap-1.5 sm:hidden"
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
        <nav className="flex flex-wrap items-center justify-center gap-3 border-t border-[var(--border)] px-6 py-4 text-sm text-[var(--text)] sm:hidden">
          <NavLinks />
        </nav>
      )}
    </header>
  );
}

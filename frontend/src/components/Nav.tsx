import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { useLanguage } from "../i18n/LanguageContext";
import { useShake } from "../lib/useShake";
import { menuItem, menuPanel } from "../lib/menuMotion";
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

function DockUnderline() {
  return (
    <span
      aria-hidden="true"
      className="absolute -bottom-0.5 left-1/2 h-px w-[calc(100%-0.75rem)] origin-left -translate-x-1/2 scale-x-0 bg-[var(--accent)] transition-transform duration-300 ease-out group-hover:scale-x-100"
    />
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
      className="group relative flex h-9 items-center gap-1.5 px-3 text-sm leading-none text-[var(--text)] transition-colors hover:text-[var(--accent)] cursor-pointer"
    >
      <GlobeIcon />
      <span className="leading-none">{current}</span>
      <DockUnderline />
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
      className="group relative flex h-9 w-9 items-center justify-center text-[var(--text)] transition-colors hover:text-[var(--accent)] cursor-pointer"
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
      <DockUnderline />
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
        className="group relative flex h-9 items-center gap-1.5 px-3 text-sm leading-none text-[var(--text)] transition-colors hover:text-[var(--accent)] cursor-pointer"
      >
        <DocsIcon />
        <span className="leading-none">DOCS</span>
        <DockUnderline />
      </Link>
    </motion.div>
  );
}

function DockDivider() {
  return <span aria-hidden="true" className="h-5 w-px shrink-0 bg-[var(--border)]" />;
}

function DesktopNavDock() {
  const location = useLocation();
  const isDocs = location.pathname.startsWith("/docs");

  const items = isDocs
    ? [
        { key: "github", node: <DockGithubLink /> },
        { key: "lang", node: <DockLanguageButton /> },
      ]
    : [
        { key: "lang", node: <DockLanguageButton /> },
        { key: "github", node: <DockGithubLink /> },
        { key: "docs", node: <DockDocsLink /> },
      ];

  return (
    <div className="flex items-center gap-1">
      {items.map((item, index) => (
        <motion.div key={item.key} variants={menuItem} className="flex items-center gap-1">
          {index > 0 && <DockDivider />}
          {item.node}
        </motion.div>
      ))}
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

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="mobile-menu"
            variants={menuPanel}
            initial="hidden"
            animate="show"
            exit="hidden"
            className="overflow-hidden sm:hidden"
          >
            <nav className="flex items-center justify-center border-t border-[var(--border)] px-6 py-4 text-sm text-[var(--text)]">
              <DesktopNavDock />
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}

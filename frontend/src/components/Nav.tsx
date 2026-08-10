import { useState } from "react";
import logo from "../assets/sentry-icon-white.png";
import wordmark from "../assets/sentry-wordmark.png";

function NavLinks({ className = "" }: { className?: string }) {
  return (
    <>
      <button className={`flex items-center gap-1 hover:text-[var(--text-h)] ${className}`}>
        Português
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
          <path d="M1 3l4 4 4-4" stroke="currentColor" strokeWidth="1.2" />
        </svg>
      </button>
      <a
        href="https://github.com"
        className={`flex items-center gap-1 hover:text-[var(--text-h)] ${className}`}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.09 3.29 9.4 7.86 10.93.57.1.78-.25.78-.55v-2.13c-3.2.7-3.87-1.36-3.87-1.36-.53-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.68 1.24 3.33.95.1-.74.4-1.24.72-1.53-2.55-.29-5.23-1.28-5.23-5.68 0-1.25.45-2.28 1.18-3.08-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.18a10.9 10.9 0 0 1 5.74 0c2.19-1.49 3.15-1.18 3.15-1.18.62 1.59.23 2.76.11 3.05.74.8 1.18 1.83 1.18 3.08 0 4.41-2.69 5.39-5.25 5.67.41.36.78 1.06.78 2.14v3.17c0 .3.21.66.79.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
        </svg>
        14 ★
      </a>
      <a
        href="#docs"
        className={`rounded-md bg-[var(--text-h)] px-3 py-1.5 text-[var(--bg)] hover:opacity-90 ${className}`}
      >
        Docs
      </a>
    </>
  );
}

export function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="border-b border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2.5">
          <img src={logo} alt="" aria-hidden="true" className="h-[37px] w-[37px] object-contain" />
          <img src={wordmark} alt="Sentry" className="h-[26px] w-auto object-contain" />
        </div>

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

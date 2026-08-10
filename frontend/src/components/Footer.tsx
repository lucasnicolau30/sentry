import logo from "../assets/sentry-icon-white.png";
import wordmark from "../assets/sentry-wordmark.png";

export function Footer({ onDocsClick }: { onDocsClick: () => void }) {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-10 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-2.5">
          <img src={logo} alt="" aria-hidden="true" className="h-6 w-6 object-contain" />
          <img src={wordmark} alt="Sentry" className="h-[18px] w-auto object-contain" />
        </div>

        <div className="flex flex-col gap-2 text-sm text-[var(--text)] sm:items-end">
          <p className="text-[var(--accent)]">
            <span className="text-[var(--text)]">$</span> pip install sentry-test
          </p>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/lucasnicolau30/sentry"
              target="_blank"
              rel="noreferrer"
              className="transition-colors hover:text-[var(--accent)]"
            >
              GitHub
            </a>
            <button type="button" onClick={onDocsClick} className="transition-colors hover:text-[var(--accent)]">
              Docs
            </button>
          </div>
        </div>
      </div>

      <div className="border-t border-[var(--border)] px-6 py-4">
        <p className="mx-auto max-w-5xl text-xs text-[var(--text)]/60">
          <span className="text-[var(--accent)]">sentry@cli</span>:~ $ MIT License · local-first, sem telemetria
        </p>
      </div>
    </footer>
  );
}

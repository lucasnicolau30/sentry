import { Link, useLocation } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext";
import logo from "../assets/sentry-icon.png";
import wordmark from "../assets/sentry-wordmark.png";

export function Footer() {
  const { t } = useLanguage();
  const location = useLocation();
  const isDocs = location.pathname.startsWith("/docs");

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }

  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-10 sm:flex-row sm:items-start sm:justify-between">
        <div>
          {isDocs ? (
            <Link to="/" onClick={scrollToTop} className="flex w-fit cursor-pointer items-center gap-2.5">
              <img src={logo} alt="" aria-hidden="true" className="h-8 w-8 object-contain" />
              <img src={wordmark} alt="Sentry" className="h-[18px] w-auto object-contain" />
            </Link>
          ) : (
            <div className="flex items-center gap-2.5">
              <img src={logo} alt="" aria-hidden="true" className="h-8 w-8 object-contain" />
              <img src={wordmark} alt="Sentry" className="h-[18px] w-auto object-contain" />
            </div>
          )}
          <p className="mt-3 text-xs text-[var(--text)]/60">
            <span className="text-[var(--accent)]">sentry@cli:~ $</span> MIT License · {t("local-first, sem telemetria", "local-first, no telemetry")}
          </p>
        </div>

        <div className="flex flex-col gap-2 text-sm text-[var(--text)] sm:items-end">
          <p className="text-[var(--text)]">
            <span className="text-[var(--accent)]">$</span> pip install sentry-test
          </p>
          <div className="flex items-center gap-4">
            {isDocs && (
              <Link
                to="/"
                onClick={scrollToTop}
                className="tab-btn cursor-pointer transition-all duration-150 hover:text-[var(--accent)] active:scale-95"
              >
                {t("Início", "Home")}
              </Link>
            )}
            <a
              href="https://github.com/lucasnicolau30/sentry"
              target="_blank"
              rel="noreferrer"
              className="tab-btn cursor-pointer transition-all duration-150 hover:text-[var(--accent)] active:scale-95"
            >
              GitHub
            </a>
            {!isDocs && (
              <Link
                to="/docs"
                onClick={scrollToTop}
                className="tab-btn cursor-pointer transition-all duration-150 hover:text-[var(--accent)] active:scale-95"
              >
                Docs
              </Link>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
}

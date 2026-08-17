import type { AnchorHTMLAttributes, ReactNode } from "react";
import { Link, useLocation, type LinkProps } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext";
import logo from "../assets/sentry-icon.png";
import wordmark from "../assets/sentry-wordmark.png";

const footerLinkClassName =
  "group relative inline-block cursor-pointer text-[var(--text)] transition-colors duration-200 hover:text-[var(--accent)] active:scale-95";

function FooterLinkUnderline() {
  return (
    <span
      aria-hidden="true"
      className="absolute -bottom-1 left-0 h-px w-full origin-left scale-x-0 bg-[var(--accent)] transition-transform duration-300 ease-out group-hover:scale-x-100"
    />
  );
}

function FooterRouteLink({ children, ...props }: { children: ReactNode } & LinkProps) {
  return (
    <Link className={footerLinkClassName} {...props}>
      {children}
      <FooterLinkUnderline />
    </Link>
  );
}

function FooterExternalLink({ children, ...props }: { children: ReactNode } & AnchorHTMLAttributes<HTMLAnchorElement>) {
  return (
    <a className={footerLinkClassName} {...props}>
      {children}
      <FooterLinkUnderline />
    </a>
  );
}

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
              <FooterRouteLink to="/" onClick={scrollToTop}>
                {t("Início", "Home")}
              </FooterRouteLink>
            )}
            <FooterExternalLink href="https://github.com/lucasnicolau30/sentry" target="_blank" rel="noreferrer">
              GitHub
            </FooterExternalLink>
            {!isDocs && (
              <FooterRouteLink to="/docs" onClick={scrollToTop}>
                Docs
              </FooterRouteLink>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
}

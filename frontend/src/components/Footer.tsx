import type { AnchorHTMLAttributes, ReactNode } from "react";
import { Link, useLocation, type LinkProps } from "react-router-dom";
import { Package } from "lucide-react";
import { motion } from "motion/react";
import { useLanguage } from "../i18n/LanguageContext";
import { useShake } from "../lib/useShake";
import logo from "../assets/sentry-icon.png";
import wordmark from "../assets/sentry-wordmark.png";

const footerLinkClassName =
  "group relative inline-block cursor-pointer text-[var(--text)] transition-colors duration-200 hover:text-[var(--accent)] active:scale-95";

function GithubIcon() {
  return (
    <svg
      aria-hidden="true"
      className="h-5 w-5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
    </svg>
  );
}
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
  const githubShake = useShake();
  const pypiShake = useShake();

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
          <p className="mt-3 text-justify text-xs leading-relaxed text-[var(--text)]/60">
            <span>© 2026 Sentry</span>
            <br />
            {t("MIT License · Versão 2.1.0 · Local-first, sem telemetria", "MIT License · Version 2.1.0 · Local-first, no telemetry")}
          </p>
        </div>

        <div className="flex w-full flex-col items-end gap-4 text-sm text-[var(--text)] sm:w-auto sm:min-w-64">
          <div className="flex items-center gap-3">
            <motion.a
              href="https://github.com/lucasnicolau30/sentry"
              target="_blank"
              rel="noreferrer"
              onClick={githubShake.shake}
              animate={githubShake.controls}
              aria-label="GitHub"
              className="flex h-9 w-9 items-center justify-center rounded-full text-[var(--text)] transition-colors hover:bg-[var(--bg)] hover:text-[var(--accent)] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
            >
              <GithubIcon />
            </motion.a>
            <motion.a
              href="https://pypi.org/project/sentry-test/#description"
              target="_blank"
              rel="noreferrer"
              onClick={pypiShake.shake}
              animate={pypiShake.controls}
              aria-label="PyPI"
              className="flex h-9 w-9 items-center justify-center rounded-full text-[var(--text)] transition-colors hover:bg-[var(--bg)] hover:text-[var(--accent)] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
            >
              <Package aria-hidden="true" className="h-5 w-5" strokeWidth={1.8} />
            </motion.a>
          </div>
          <nav aria-label="Footer" className="flex flex-wrap justify-end gap-x-5 gap-y-2">
            {isDocs ? (
              <FooterRouteLink to="/" onClick={scrollToTop}>
                {t("Início", "Home")}
              </FooterRouteLink>
            ) : (
              <FooterRouteLink to="/docs" onClick={scrollToTop}>
                Docs
              </FooterRouteLink>
            )}
            <FooterExternalLink href="https://github.com/lucasnicolau30/sentry/issues" target="_blank" rel="noreferrer">
              {t("Reportar problema", "Report an issue")}
            </FooterExternalLink>
            <FooterExternalLink href="mailto:nicolau.lucas04@gmail.com">
              {t("Contato", "Contact")}
            </FooterExternalLink>
          </nav>
        </div>
      </div>
    </footer>
  );
}

import { InstallCommand } from "./InstallCommand";
import { TerminalWindow } from "./TerminalWindow";
import { useLanguage } from "../i18n/LanguageContext";

const heroLines = {
  pt: [
    { text: "sentry run --spec cadastro-de-cliente --run-tests", tone: "command" as const },
    { text: "[INFO] Lendo diff e cobertura...", tone: "info" as const },
    { text: "[INFO] 4 casos ligados a testes reais.", tone: "info" as const },
    { text: "[SUCCESS] Cobertura do código alterado: 92%.", tone: "success" as const },
    { text: "[SUCCESS] Veredito: aprovado.", tone: "success" as const },
  ],
  en: [
    { text: "sentry run --spec customer-registration --run-tests", tone: "command" as const },
    { text: "[INFO] Reading diff and coverage...", tone: "info" as const },
    { text: "[INFO] 4 cases linked to real tests.", tone: "info" as const },
    { text: "[SUCCESS] Changed code coverage: 92%.", tone: "success" as const },
    { text: "[SUCCESS] Verdict: passed.", tone: "success" as const },
  ],
};

export function Hero() {
  const { lang, t } = useLanguage();

  return (
    <section className="relative mx-auto max-w-5xl overflow-hidden px-6 pt-20 pb-4">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-24 left-1/2 h-[420px] w-[720px] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(34,197,94,0.18),rgba(34,197,94,0.06),transparent)] blur-3xl"
      />

      <div className="relative flex flex-col items-center text-center">
        <span
          aria-hidden="true"
          className="absolute -top-3 left-0 h-4 w-4 border-t-2 border-l-2 border-[var(--accent)]/60"
        />
        <span
          aria-hidden="true"
          className="absolute -top-3 right-0 h-4 w-4 border-t-2 border-r-2 border-[var(--accent)]/60"
        />
        <span
          aria-hidden="true"
          className="absolute -bottom-3 left-0 h-4 w-4 border-b-2 border-l-2 border-[var(--accent)]/60"
        />
        <span
          aria-hidden="true"
          className="absolute -bottom-3 right-0 h-4 w-4 border-b-2 border-r-2 border-[var(--accent)]/60"
        />

        <h1 className="max-w-2xl text-4xl font-semibold uppercase leading-tight tracking-normal sm:text-5xl">
          {t("A disciplina entre", "The discipline between")}
          <br />
          {t("o commit e a confiança", "commit and confidence")}
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-[var(--accent)] sm:text-lg">
          {t(
            "O agente de IA declara a intenção; o Sentry mede a realidade: roda a suíte, lê o diff e a cobertura, e emite um veredito auditável.",
            "The AI agent declares intent; Sentry measures reality: it runs the suite, reads the diff and coverage, and issues an auditable verdict."
          )}
        </p>

        <div className="mt-8">
          <InstallCommand />
        </div>

        <div className="mt-10 w-full max-w-lg text-left">
          <TerminalWindow lines={heroLines[lang]} title="sentry" />
        </div>
      </div>
    </section>
  );
}

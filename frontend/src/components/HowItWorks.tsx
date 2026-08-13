import { useLanguage } from "../i18n/LanguageContext";

const iconProps = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const NewIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M12 5v14M5 12h14" />
  </svg>
);

const CheckSquareIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <rect x="4" y="4" width="16" height="16" rx="3" />
    <path d="M8.5 12l2.3 2.3L16 9" />
  </svg>
);

const RunIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M6 4l14 8-14 8V4z" />
  </svg>
);

const ReportIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M6 3h9l4 4v14H6V3z" />
    <path d="M9 12h6M9 16h6M9 8h3" />
  </svg>
);

const Arrow = () => (
  <svg
    aria-hidden="true"
    className="hidden shrink-0 text-[var(--accent)] sm:block"
    width="40"
    height="16"
    viewBox="0 0 40 16"
    fill="none"
  >
    <path d="M0 8h34M28 2l6 6-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const steps = {
  pt: [
    {
      icon: <NewIcon />,
      command: "sentry new",
      title: "Cria a spec",
      description: (
        <>
          Gera <span className="text-[var(--text-h)]">PROMPT.md</span> e <span className="text-[var(--text-h)]">CASES.md</span> em
          branco para a mudança.
        </>
      ),
    },
    {
      icon: <CheckSquareIcon />,
      command: "sentry check",
      title: "Valida a matriz",
      description: "Estrutura, vocabulário e classes de equivalência do catálogo.",
    },
    {
      icon: <RunIcon />,
      command: "sentry run --run-tests",
      title: "Roda a suíte",
      description: "Lê diff e cobertura, aplica as regras, emite o veredito.",
    },
    {
      icon: <ReportIcon />,
      command: "sentry report",
      title: "Audita o resultado",
      description: "Releitura do veredito e comparação entre execuções.",
    },
  ],
  en: [
    {
      icon: <NewIcon />,
      command: "sentry new",
      title: "Creates the spec",
      description: (
        <>
          Generates a blank <span className="text-[var(--text-h)]">PROMPT.md</span> and{" "}
          <span className="text-[var(--text-h)]">CASES.md</span> for the change.
        </>
      ),
    },
    {
      icon: <CheckSquareIcon />,
      command: "sentry check",
      title: "Validates the matrix",
      description: "Structure, vocabulary and catalog equivalence classes.",
    },
    {
      icon: <RunIcon />,
      command: "sentry run --run-tests",
      title: "Runs the suite",
      description: "Reads diff and coverage, applies the rules, issues the verdict.",
    },
    {
      icon: <ReportIcon />,
      command: "sentry report",
      title: "Audits the result",
      description: "Reads back the verdict and compares runs.",
    },
  ],
};

export function HowItWorks() {
  const { lang, t } = useLanguage();
  const items = steps[lang];

  return (
    <section className="mx-auto max-w-5xl px-6 py-14">
      <h2 className="text-center text-2xl font-semibold uppercase tracking-normal sm:text-3xl">
        {t("Como funciona", "How it works")}
      </h2>
      <p className="mx-auto mt-2 max-w-xl text-center text-sm text-[var(--text)]/60 sm:text-base">
        {t("Quatro comandos entre o pedido e o veredito auditável.", "Four commands between the request and the auditable verdict.")}
      </p>

      <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-4 sm:gap-2">
        {items.map((step, index) => (
          <div key={step.command} className="flex items-start gap-4 sm:flex-col sm:items-center sm:text-center">
            <div className="flex items-center gap-2 sm:w-full sm:justify-center">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-alt)] text-[var(--accent)]">
                {step.icon}
              </div>
              {index < items.length - 1 && <Arrow />}
            </div>
            <div className="sm:mt-3">
              <code className="font-mono text-xs text-[var(--text-h)]">
                <span className="text-[var(--accent)]">$ </span>
                {step.command}
              </code>
              <h3 className="mt-1 text-sm font-semibold">
                {index + 1}. {step.title}
              </h3>
              <p className="mt-1 text-sm leading-relaxed text-[var(--text)]/60">{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

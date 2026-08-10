import type { ReactNode } from "react";
import { useState } from "react";

const iconProps = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const ExternalIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M7 17L17 7M8 7h9v9" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const DownloadIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M12 3v12m0 0l-4-4m4 4l4-4" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
  </svg>
);

const SlidersIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M4 6h10M17 6h3M4 12h3M9 12h11M4 18h7M14 18h6" strokeLinecap="round" />
    <circle cx="16" cy="6" r="2" />
    <circle cx="7" cy="12" r="2" />
    <circle cx="12" cy="18" r="2" />
  </svg>
);

const FlowIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M6 3v6a3 3 0 003 3h6a3 3 0 013 3v6" strokeLinecap="round" />
    <circle cx="6" cy="3" r="2" />
    <circle cx="18" cy="21" r="2" />
  </svg>
);

const TerminalIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <path d="M7 10l3 2-3 2M12 14h5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const PenIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M4 20l4-1 11-11-3-3L5 16l-1 4z" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ScanIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M4 8V5a1 1 0 011-1h3M20 8V5a1 1 0 00-1-1h-3M4 16v3a1 1 0 001 1h3M20 16v3a1 1 0 01-1 1h-3" strokeLinecap="round" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const RunIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M6 4l14 8-14 8V4z" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ReportIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M7 3h7l4 4v13a1 1 0 01-1 1H7a1 1 0 01-1-1V4a1 1 0 011-1z" strokeLinejoin="round" />
    <path d="M9 12h6M9 16h6" strokeLinecap="round" />
  </svg>
);

const HistoryIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 3" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const BranchIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <circle cx="6" cy="6" r="2" />
    <circle cx="6" cy="18" r="2" />
    <circle cx="18" cy="12" r="2" />
    <path d="M6 8v8M6 8c0 4 4 4 10 4" strokeLinecap="round" />
  </svg>
);

const PackageIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M12 3l8 4v10l-8 4-8-4V7l8-4z" strokeLinejoin="round" />
    <path d="M4 7l8 4 8-4M12 11v10" strokeLinecap="round" />
  </svg>
);

const IssueIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v5M12 16h.01" strokeLinecap="round" />
  </svg>
);

const CopyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="2" />
    <path
      d="M6 15H4.8A1.8 1.8 0 0 1 3 13.2V4.8A1.8 1.8 0 0 1 4.8 3h8.4A1.8 1.8 0 0 1 15 4.8V6"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M4 12l5 5L20 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

function CodeBlock({ lines }: { lines: string[] }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(lines[0]);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] px-4 py-3.5 font-mono text-sm text-[var(--text-h)]">
      <div className="space-y-0.5">
        {lines.map((line, index) => (
          <p key={index} className={index === 0 ? "" : "text-[var(--text)]/50"}>
            {index === 0 ? line : `# ${line}`}
          </p>
        ))}
      </div>
      <button
        type="button"
        onClick={handleCopy}
        aria-label="Copiar comando"
        className="shrink-0 cursor-pointer text-[var(--accent)] transition-colors hover:text-[var(--text-h)]"
      >
        {copied ? <CheckIcon /> : <CopyIcon />}
      </button>
    </div>
  );
}

function PageFooter({ nextLabel, onNextClick }: { nextLabel: string; onNextClick: () => void }) {
  return (
    <div className="mt-16 border-t border-[var(--border)] pt-6 text-right">
      <p className="text-xs text-[var(--text)]/50">Próxima</p>
      <button
        type="button"
        onClick={onNextClick}
        className="mt-1 inline-flex items-center gap-1.5 text-base font-medium text-[var(--text-h)] transition-colors hover:text-[var(--accent)]"
      >
        {nextLabel} <span aria-hidden="true">→</span>
      </button>
    </div>
  );
}

type Card = { icon: ReactNode; title: string; description: string; external?: boolean; href?: string };

function DocCard({ icon, title, description, external, href }: Card) {
  const content = (
    <>
      <div className="mb-3 flex items-center justify-between text-[var(--accent)]">
        {icon}
        {external && <span className="text-[var(--text)]/50">{<ExternalIcon />}</span>}
      </div>
      <h3 className="mb-1.5 text-sm font-semibold text-[var(--text-h)]">{title}</h3>
      <p className="text-sm leading-relaxed text-[var(--text)]/70">{description}</p>
    </>
  );

  if (href) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="block rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] p-5 transition-colors duration-200 hover:border-[var(--accent)]/40"
      >
        {content}
      </a>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] p-5 transition-colors duration-200 hover:border-[var(--accent)]/40">
      {content}
    </div>
  );
}

const tabs = ["Comece aqui", "Visão geral", "Setup e configuração", "O fluxo de trabalho", "Comandos e Habilidades"];

const principles: Card[] = [
  {
    icon: <PenIcon />,
    title: "O markdown é a fonte da intenção",
    description:
      "CASES.md e PROMPT.md vivem em .sentry/specs/ como markdown puro. A CLI lê e valida esses arquivos; ela nunca os escreve.",
  },
  {
    icon: <SlidersIcon />,
    title: "Determinístico e auditável",
    description:
      "Dez regras com severidade configurável. O Sentry nunca chama um modelo, então cada veredito é reproduzível.",
  },
];

const actions: Card[] = [
  {
    icon: <TerminalIcon />,
    title: "Inicialize o repositório",
    description: "sentry init cria .sentry/, sentry.toml, o guia de agente e as skills, sem sobrescrever o que já existe.",
  },
  {
    icon: <ScanIcon />,
    title: "Declare a intenção",
    description: "sentry new \"nome\" cria a pasta da spec com PROMPT.md preservado e CASES.md em branco.",
  },
  {
    icon: <FlowIcon />,
    title: "Valide a estrutura",
    description: "sentry check confere vocabulário, estrutura e cobrança das classes de equivalência antes de rodar.",
  },
  {
    icon: <RunIcon />,
    title: "Rode a suíte",
    description: "sentry run --run-tests executa os testes, lê diff e cobertura, aplica as regras e persiste o resultado.",
  },
  {
    icon: <ReportIcon />,
    title: "Leia o veredito",
    description: "sentry report exibe o último relatório com as quatro dimensões de cobertura e a evidência de cada achado.",
  },
  {
    icon: <HistoryIcon />,
    title: "Compare o histórico",
    description: "sentry history lista execuções e compara as duas últimas: cobertura, testes e achados lado a lado.",
  },
];

const firstSteps: Card[] = [
  {
    icon: <DownloadIcon />,
    title: "Instalação",
    description: "pip install sentry-test. Requer Python 3.11+; confirme com sentry --version.",
  },
  {
    icon: <SlidersIcon />,
    title: "Setup",
    description: "sentry init [--install] prepara o repositório e escreve o fluxo para o seu agente de IA.",
  },
  {
    icon: <FlowIcon />,
    title: "O fluxo de trabalho",
    description: "Os cinco passos: declarar, validar, ligar ao teste, rodar e comparar histórico.",
  },
  {
    icon: <TerminalIcon />,
    title: "Comandos e Habilidades",
    description: "Referência completa de init, new, check, run, report, history e clear.",
  },
];

const learnMore: Card[] = [
  {
    icon: <BranchIcon />,
    title: "Repositório",
    description: "Leia o código, abra issues e dê uma estrela no GitHub.",
    href: "https://github.com/lucasnicolau30/sentry",
    external: true,
  },
  {
    icon: <PackageIcon />,
    title: "Pacote PyPI",
    description: "Instale o sentry-test direto do índice do PyPI.",
    href: "https://pypi.org/project/sentry-test/",
    external: true,
  },
  {
    icon: <IssueIcon />,
    title: "Reporte um problema",
    description: "Encontrou um bug ou tem uma ideia? Abra uma issue no GitHub.",
    href: "https://github.com/lucasnicolau30/sentry/issues",
    external: true,
  },
];

function GetStartedContent({ onNextClick }: { onNextClick: () => void }) {
  return (
    <div className="mx-auto max-w-5xl px-6 py-14">
      <h2 className="mb-4 text-xl font-semibold text-[var(--text-h)]">O que é o sentry?</h2>
      <p className="max-w-3xl text-[15px] leading-relaxed text-[var(--text)]/80">
        O sentry é uma CLI de qualidade de teste orientada a mudança. O agente de IA declara a intenção em
        markdown; o sentry mede a realidade: roda a suíte, lê o diff e a cobertura, e emite um veredito
        auditável.
      </p>

      <div className="mt-6 max-w-lg rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] p-5 font-mono text-sm leading-relaxed text-[var(--text)]/80">
        <p>.sentry/specs/cadastro-de-cliente/</p>
        <p className="pl-4">PROMPT.md</p>
        <p className="pl-4">CASES.md</p>
        <p>.sentry/reports/</p>
        <p className="pl-4 text-[var(--accent)]">latest.md</p>
      </div>

      <h2 className="mb-4 mt-14 text-xl font-semibold text-[var(--text-h)]">Princípios do sentry</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {principles.map((card) => (
          <DocCard key={card.title} {...card} />
        ))}
      </div>

      <h2 className="mb-4 mt-14 text-xl font-semibold text-[var(--text-h)]">O que você pode fazer</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {actions.map((card) => (
          <DocCard key={card.title} {...card} />
        ))}
      </div>

      <h2 className="mb-4 mt-14 text-xl font-semibold text-[var(--text-h)]">Primeiros passos</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {firstSteps.map((card) => (
          <DocCard key={card.title} {...card} />
        ))}
      </div>

      <h2 className="mb-4 mt-14 text-xl font-semibold text-[var(--text-h)]">Saiba mais sobre o sentry</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {learnMore.map((card) => (
          <DocCard key={card.title} {...card} />
        ))}
      </div>

      <PageFooter nextLabel="Visão geral" onNextClick={onNextClick} />
    </div>
  );
}

const overviewSections = [
  { id: "comece-a-usar", label: "Comece a usar" },
  { id: "instale-a-cli", label: "Instale a CLI" },
  { id: "verifique", label: "Verifique" },
];

function OverviewContent({ onNextClick }: { onNextClick: () => void }) {
  return (
    <div className="mx-auto max-w-5xl px-6 py-14">
      <div className="flex gap-12">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--accent)]">Primeiros passos</p>
          <h1 className="mt-2 text-3xl font-semibold text-[var(--text-h)]">Visão geral</h1>
          <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[var(--text)]/80">
            O sentry é uma CLI de qualidade de teste orientada a mudança. Ela cria a pasta da spec, valida a
            matriz de casos em markdown e acompanha cobertura e veredito, mantendo o markdown como única
            fonte da intenção.
          </p>

          <h2 id="comece-a-usar" className="mb-2 mt-12 text-lg font-semibold text-[var(--text-h)]">
            Comece a usar
          </h2>
          <p className="max-w-2xl text-[15px] leading-relaxed text-[var(--text)]/80">
            O sentry requer Python 3.11 ou superior. Siga os passos abaixo para instalar e verificar seu
            setup.
          </p>

          <h2 id="instale-a-cli" className="mb-2 mt-10 text-lg font-semibold text-[var(--text-h)]">
            Instale a CLI
          </h2>
          <p className="mb-3 text-[15px] leading-relaxed text-[var(--text)]/80">Instale o pacote via pip:</p>
          <CodeBlock lines={["pip install sentry-test"]} />

          <h2 id="verifique" className="mb-2 mt-10 text-lg font-semibold text-[var(--text-h)]">
            Verifique
          </h2>
          <p className="mb-3 text-[15px] leading-relaxed text-[var(--text)]/80">
            Confirme que a CLI está disponível no seu PATH:
          </p>
          <CodeBlock lines={["sentry --version", "sentry-test x.y.z"]} />

          <PageFooter nextLabel="Setup e configuração" onNextClick={onNextClick} />
        </div>

        <aside className="hidden w-48 shrink-0 lg:block">
          <div className="sticky top-6">
            <p className="mb-3 flex items-center gap-1.5 text-xs text-[var(--text)]/50">
              <TerminalIcon /> Nesta página
            </p>
            <ul className="space-y-2.5 border-l border-[var(--border)] pl-4 text-sm">
              {overviewSections.map((section, index) => (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    className={index === 0 ? "font-medium text-[var(--text-h)]" : "text-[var(--text)]/60 hover:text-[var(--text)]"}
                  >
                    {section.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}

export function DocsPage() {
  const [activeTab, setActiveTab] = useState(tabs[0]);

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <div className="border-b border-[var(--border)]">
        <nav className="mx-auto flex max-w-5xl items-center gap-6 overflow-x-auto px-6 text-sm">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`whitespace-nowrap border-b-2 py-3 transition-colors ${
                activeTab === tab
                  ? "border-[var(--accent)] text-[var(--text-h)]"
                  : "border-transparent text-[var(--text)]/60 hover:text-[var(--text)]"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === "Comece aqui" && (
        <>
          <div className="relative overflow-hidden border-b border-[var(--border)]">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute -top-24 left-1/2 h-[360px] w-[720px] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(34,197,94,0.18),rgba(34,197,94,0.06),transparent)] blur-3xl"
            />
            <div className="relative mx-auto max-w-5xl px-6 py-20 text-center">
              <h1 className="text-3xl font-semibold text-[var(--text-h)] sm:text-4xl">
                Bem-vindo à documentação do <span className="text-[var(--accent)]">sentry</span>
              </h1>
              <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-[var(--text)]/70">
                Instale a CLI, escreva a spec com seu agente de IA e rode o ciclo intenção → veredito direto
                do terminal.
              </p>
            </div>
          </div>
          <GetStartedContent onNextClick={() => setActiveTab("Visão geral")} />
        </>
      )}

      {activeTab === "Visão geral" && (
        <OverviewContent onNextClick={() => setActiveTab("Setup e configuração")} />
      )}

      {activeTab !== "Comece aqui" && activeTab !== "Visão geral" && (
        <div className="mx-auto max-w-5xl px-6 py-20 text-center text-[var(--text)]/60">Em construção.</div>
      )}
    </div>
  );
}

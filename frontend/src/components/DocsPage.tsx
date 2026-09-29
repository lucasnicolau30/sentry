import type { ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { menuItem, menuPanel } from "../lib/menuMotion";
import { TerminalWindow } from "./TerminalWindow";
import { Reveal } from "./Reveal";
import { BlurReveal } from "./blur-reveal";
import { TextMarquee } from "./TextMarquee";
import { useLanguage } from "../i18n/LanguageContext";

const SCROLL_SPY_OFFSET = 120;

function useScrollSpy(ids: string[]) {
  const [activeId, setActiveId] = useState(ids[0]);

  useEffect(() => {
    setActiveId(ids[0]);

    function update() {
      const atBottom =
        window.innerHeight + window.scrollY >=
        document.documentElement.scrollHeight - 2;
      if (atBottom) {
        setActiveId(ids[ids.length - 1]);
        return;
      }

      let current = ids[0];
      for (const id of ids) {
        const el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top <= SCROLL_SPY_OFFSET) {
          current = id;
        }
      }
      setActiveId(current);
    }

    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [ids]);

  return activeId;
}

function DocsSidebar({
  sections,
  label,
}: {
  sections: { id: string; label: string }[];
  label: string;
}) {
  const ids = useMemo(() => sections.map((s) => s.id), [sections]);
  const activeId = useScrollSpy(ids);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [indicator, setIndicator] = useState({ top: 0, height: 0 });
  const itemRefs = useRef<Record<string, HTMLAnchorElement | null>>({});
  const targetId = hoverId ?? activeId;

  useEffect(() => {
    const el = itemRefs.current[targetId];
    if (el) {
      setIndicator({ top: el.offsetTop, height: el.offsetHeight });
    }
  }, [targetId, sections]);

  return (
    <aside className="hidden w-48 shrink-0 md:block">
      <div className="sticky top-6">
        <p className="mb-3 flex items-center gap-1.5 text-xs text-[var(--text)]/50">
          <span className="text-[var(--accent)]">
            <TerminalIcon />
          </span>{" "}
          {label}
        </p>
        <ul
          className="relative space-y-2.5 border-l border-[var(--border)] pl-4 text-sm"
          onMouseLeave={() => setHoverId(null)}
        >
          <span
            aria-hidden="true"
            className="pointer-events-none absolute -left-px w-[1.5px] rounded-full bg-[var(--accent)] transition-all duration-200 ease-out"
            style={{ top: indicator.top, height: indicator.height }}
          />
          {sections.map((section) => (
            <li key={section.id}>
              <a
                href={`#${section.id}`}
                ref={(el) => {
                  itemRefs.current[section.id] = el;
                }}
                onMouseEnter={() => setHoverId(section.id)}
                className={`inline-block cursor-pointer transition-all duration-150 active:scale-95 ${
                  activeId === section.id
                    ? "font-medium text-[var(--accent)]"
                    : "text-[var(--text)]/60 hover:text-[var(--accent)]"
                }`}
              >
                {section.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

// Mesma arte e mesmas três faixas de verde que a CLI imprime no `init`
// (`_WORDMARK_LINES` / `_WORDMARK_BANDS` em src/sentrytest/adapters/terminal.py):
// duas linhas de verde vivo, duas de verde normal, duas de verde apagado, com a
// versão colada no pé da última linha — na faixa do meio, como no terminal.
const wordmarkLines = [
  "███████╗███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗",
  "██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝",
  "███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝ ╚████╔╝ ",
  "╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝  ",
  "███████║███████╗██║ ╚████║   ██║   ██║  ██║   ██║   ",
  "╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝",
];

const wordmarkBands = ["banner-bright", "banner-mid", "banner-dim"] as const;

// As cinco primeiras linhas saem diretas; a sexta vem com a versão no mesmo
// parágrafo, porque a CLI também cola a versão na mesma linha do rodapé.
const wordmarkLine = (index: number) => ({
  text: wordmarkLines[index],
  tone: wordmarkBands[
    Math.min(Math.floor(index / 2), wordmarkBands.length - 1)
  ],
});

const wordmarkFooter = {
  tone: "banner-mid" as const,
  segments: [
    { text: wordmarkLines[5], tone: "banner-dim" as const },
    { text: "  v2.1.0", tone: "banner-mid" as const },
  ],
};

const heroLines = {
  pt: [
    { text: "sentry init", tone: "command" as const },
    { text: "", tone: "muted" as const },
    ...[0, 1, 2, 3, 4].map(wordmarkLine),
    wordmarkFooter,
    {
      text: "[INFO] Criando .sentry/, sentry.toml e as skills...",
      tone: "info" as const,
    },
    {
      text: "[SUCCESS] Repositório pronto para declarar intenção.",
      tone: "success" as const,
    },
  ],
  en: [
    { text: "sentry init", tone: "command" as const },
    { text: "", tone: "muted" as const },
    ...[0, 1, 2, 3, 4].map(wordmarkLine),
    wordmarkFooter,
    {
      text: "[INFO] Creating .sentry/, sentry.toml and the skills...",
      tone: "info" as const,
    },
    {
      text: "[SUCCESS] Repository ready to declare intent.",
      tone: "success" as const,
    },
  ],
};

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
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    aria-hidden="true"
  >
    <path d="M7 17L17 7M8 7h9v9" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const DownloadIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path
      d="M12 3v12m0 0l-4-4m4 4l4-4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
  </svg>
);

const SlidersIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path
      d="M4 6h10M17 6h3M4 12h3M9 12h11M4 18h7M14 18h6"
      strokeLinecap="round"
    />
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
    <path
      d="M7 10l3 2-3 2M12 14h5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const PenIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path
      d="M4 20l4-1 11-11-3-3L5 16l-1 4z"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const ScanIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path
      d="M4 8V5a1 1 0 011-1h3M20 8V5a1 1 0 00-1-1h-3M4 16v3a1 1 0 001 1h3M20 16v3a1 1 0 01-1 1h-3"
      strokeLinecap="round"
    />
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
    <path
      d="M7 3h7l4 4v13a1 1 0 01-1 1H7a1 1 0 01-1-1V4a1 1 0 011-1z"
      strokeLinejoin="round"
    />
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

const ArchiveIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path
      d="M3 7h18v3H3zM5 10v9a2 2 0 002 2h10a2 2 0 002-2v-9M10 14h4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const CopyIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    aria-hidden="true"
  >
    <rect
      x="9"
      y="9"
      width="12"
      height="12"
      rx="2"
      stroke="currentColor"
      strokeWidth="2"
    />
    <path
      d="M6 15H4.8A1.8 1.8 0 0 1 3 13.2V4.8A1.8 1.8 0 0 1 4.8 3h8.4A1.8 1.8 0 0 1 15 4.8V6"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

const CheckIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    aria-hidden="true"
  >
    <path
      d="M4 12l5 5L20 6"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

function CodeBlock({ lines }: { lines: string[] }) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(lines[0]);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] shadow-[0_0_24px_-8px_rgba(0,0,0,0.6)] transition-transform duration-300 hover:-translate-y-1">
      <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f56]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#27c93f]" />
        <span className="ml-2 font-mono text-xs text-[var(--text)]/60">
          sentry
        </span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={t("Copiar comando", "Copy command")}
          className="ml-auto shrink-0 cursor-pointer text-[var(--accent)] transition-colors hover:text-[var(--text-h)]"
        >
          {copied ? <CheckIcon /> : <CopyIcon />}
        </button>
      </div>
      <div className="space-y-0.5 px-4 py-3.5 font-mono text-base">
        {lines.map((line, index) => (
          <p
            key={index}
            className={`whitespace-pre-wrap break-words ${index === 0 ? "text-[var(--text-h)]" : "text-[var(--text)]/50"}`}
          >
            {index === 0 ? (
              <span className="text-[var(--accent)]">$ </span>
            ) : null}
            {index === 0 ? line : `# ${line}`}
          </p>
        ))}
      </div>
    </div>
  );
}

function PageFooter({
  prevLabel,
  onPrevClick,
  nextLabel,
  onNextClick,
  className = "mt-16",
}: {
  prevLabel?: string;
  onPrevClick?: () => void;
  nextLabel?: string;
  onNextClick?: () => void;
  className?: string;
}) {
  const { t } = useLanguage();
  return (
    <div
      className={`${className} flex items-start justify-between border-t border-[var(--border)] pt-6`}
    >
      {prevLabel && onPrevClick ? (
        <div className="text-left">
          <p className="text-xs text-[var(--accent)]">
            {t("Anterior", "Previous")}
          </p>
          <button
            type="button"
            onClick={onPrevClick}
            className="group mt-1 inline-flex cursor-pointer items-center gap-1.5 text-base font-medium text-[var(--text-h)] transition-colors duration-200 hover:text-[var(--accent)] active:scale-95"
          >
            <span
              aria-hidden="true"
              className="inline-block transition-transform duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] group-hover:-translate-x-1"
            >
              ←
            </span>
            <span className="relative">
              {prevLabel}
              <span
                aria-hidden="true"
                className="absolute -bottom-1 left-0 h-px w-full origin-right scale-x-0 bg-[var(--accent)] transition-transform duration-300 ease-out group-hover:scale-x-100"
              />
            </span>
          </button>
        </div>
      ) : (
        <span />
      )}

      {nextLabel && onNextClick ? (
        <div className="text-right">
          <p className="text-xs text-[var(--accent)]">{t("Próxima", "Next")}</p>
          <button
            type="button"
            onClick={onNextClick}
            className="group mt-1 inline-flex cursor-pointer items-center gap-1.5 text-base font-medium text-[var(--text-h)] transition-colors duration-200 hover:text-[var(--accent)] active:scale-95"
          >
            <span className="relative">
              {nextLabel}
              <span
                aria-hidden="true"
                className="absolute -bottom-1 left-0 h-px w-full origin-left scale-x-0 bg-[var(--accent)] transition-transform duration-300 ease-out group-hover:scale-x-100"
              />
            </span>
            <span
              aria-hidden="true"
              className="inline-block transition-transform duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] group-hover:translate-x-1"
            >
              →
            </span>
          </button>
        </div>
      ) : (
        <span />
      )}
    </div>
  );
}

type Card = {
  icon: ReactNode;
  title: ReactNode;
  description: ReactNode;
  external?: boolean;
  href?: string;
  className?: string;
};

function Cmd({ children }: { children: ReactNode }) {
  return (
    <span className="whitespace-nowrap">
      <span className="text-[var(--accent)]">$</span>&nbsp;
      <span className="text-[var(--text-h)]">{children}</span>
    </span>
  );
}

function DocCard({ icon, title, description, external, href, className = "" }: Card) {
  const content = (
    <>
      <div className="mb-3 flex items-center justify-between text-[var(--accent)]">
        {icon}
        {external && <ExternalIcon />}
      </div>
      <h3 className="mb-3 text-base font-semibold text-[var(--text-h)]">
        {title}
      </h3>
      <div className="mb-4 h-px w-6 bg-[var(--border)]" />
      <p className="text-justify text-base leading-relaxed text-[var(--text)]/70">
        {description}
      </p>
    </>
  );

  if (href) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className={`glow-card flex h-full flex-col rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] px-6 py-5 transition-colors duration-200 hover:border-[var(--accent)]/40 ${className}`}
      >
        {content}
      </a>
    );
  }

  return (
    <div
      className={`glow-card flex h-full flex-col rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] px-6 py-5 transition-colors duration-200 hover:border-[var(--accent)]/40 ${className}`}
    >
      {content}
    </div>
  );
}

const tabs = [
  { id: "start", pt: "Comece aqui", en: "Getting started" },
  { id: "setup", pt: "Setup e configuração", en: "Setup & configuration" },
  { id: "workflow", pt: "O fluxo de trabalho", en: "The workflow" },
  { id: "commands", pt: "Comandos e Habilidades", en: "Commands & Skills" },
  { id: "papers", pt: "Papers", en: "Papers" },
];

const principlesByLang: Record<"pt" | "en", Card[]> = {
  pt: [
    {
      icon: <PenIcon />,
      title: "O markdown é a fonte da intenção",
      description: (
        <>
          <span className="text-[var(--text-h)]">CASES.md</span> e{" "}
          <span className="text-[var(--text-h)]">PROMPT.md</span> vivem em{" "}
          <span className="text-[var(--text-h)]">.sentry/specs/</span> como
          markdown puro. A CLI lê e valida esses arquivos; ela nunca os escreve.
        </>
      ),
    },
    {
      icon: <SlidersIcon />,
      title: "Determinístico e auditável",
      description: (
        <>
          Dez regras com severidade configurável. O{" "}
          <span className="text-[var(--text-h)]">Sentry</span> nunca chama um
          modelo, então cada veredito é reproduzível.
        </>
      ),
    },
  ],
  en: [
    {
      icon: <PenIcon />,
      title: "Markdown is the source of intent",
      description: (
        <>
          <span className="text-[var(--text-h)]">CASES.md</span> and{" "}
          <span className="text-[var(--text-h)]">PROMPT.md</span> live in{" "}
          <span className="text-[var(--text-h)]">.sentry/specs/</span> as plain
          markdown. The CLI reads and validates these files; it never writes
          them.
        </>
      ),
    },
    {
      icon: <SlidersIcon />,
      title: "Deterministic and auditable",
      description: (
        <>
          Ten rules with configurable severity.{" "}
          <span className="text-[var(--text-h)]">Sentry</span> never calls a
          model, so every verdict is reproducible.
        </>
      ),
    },
  ],
};

const actionsByLang: Record<"pt" | "en", Card[]> = {
  pt: [
    {
      icon: <TerminalIcon />,
      title: "Inicialize o repositório",
      description: (
        <>
          <Cmd>sentry init</Cmd> cria{" "}
          <span className="text-[var(--text-h)]">.sentry/</span>,{" "}
          <span className="text-[var(--text-h)]">sentry.toml</span>, o guia de
          agente e as skills, sem sobrescrever o que já existe.
        </>
      ),
    },
    {
      icon: <ScanIcon />,
      title: "Declare a intenção",
      description: (
        <>
          <Cmd>sentry new "nome"</Cmd> cria a pasta da spec com{" "}
          <span className="text-[var(--text-h)]">PROMPT.md</span> preservado e{" "}
          <span className="text-[var(--text-h)]">CASES.md</span> em branco.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      title: "Valide a estrutura",
      description: (
        <>
          <Cmd>sentry check</Cmd> confere vocabulário, estrutura e cobrança das
          classes de equivalência antes de rodar.
        </>
      ),
    },
    {
      icon: <RunIcon />,
      title: "Feche o loop",
      description: (
        <>
          <Cmd>sentry watch</Cmd> reavalia a cada salvamento sem custo, e{" "}
          <Cmd>sentry review</Cmd> dá o veredito completo antes de commitar.
        </>
      ),
    },
    {
      icon: <ReportIcon />,
      title: "Leia o veredito",
      description: (
        <>
          <Cmd>sentry report</Cmd> exibe o último relatório com as cinco
          dimensões de cobertura e a evidência de cada achado.
        </>
      ),
    },
    {
      icon: <HistoryIcon />,
      title: "Compare o histórico",
      description: (
        <>
          <Cmd>sentry history</Cmd> lista execuções e compara as duas últimas:
          cobertura, testes e achados lado a lado.
        </>
      ),
    },
    {
      icon: <ArchiveIcon />,
      title: "Arquive a evidência",
      description: (
        <>
          <Cmd>sentry archive</Cmd> versiona print, vídeo e veredito por
          módulo, por specs certificadas ou por rota fotografada de verdade.
        </>
      ),
    },
    {
      icon: <IssueIcon />,
      title: "Enxergue a aplicação inteira",
      description: (
        <>
          <Cmd>sentry status</Cmd> mede tudo contra toda spec declarada, sempre
          pela suíte completa: a fotografia periódica, não o loop do dia a dia.
        </>
      ),
    },
  ],
  en: [
    {
      icon: <TerminalIcon />,
      title: "Initialize the repository",
      description: (
        <>
          <Cmd>sentry init</Cmd> creates{" "}
          <span className="text-[var(--text-h)]">.sentry/</span>,{" "}
          <span className="text-[var(--text-h)]">sentry.toml</span>, the agent
          guide and the skills, without overwriting what's already there.
        </>
      ),
    },
    {
      icon: <ScanIcon />,
      title: "Declare intent",
      description: (
        <>
          <Cmd>sentry new "name"</Cmd> creates the spec folder with{" "}
          <span className="text-[var(--text-h)]">PROMPT.md</span> preserved and
          a blank <span className="text-[var(--text-h)]">CASES.md</span>.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      title: "Validate the structure",
      description: (
        <>
          <Cmd>sentry check</Cmd> checks vocabulary, structure and required
          equivalence classes before running anything.
        </>
      ),
    },
    {
      icon: <RunIcon />,
      title: "Close the loop",
      description: (
        <>
          <Cmd>sentry watch</Cmd> re-evaluates on every save at no cost, and{" "}
          <Cmd>sentry review</Cmd> gives the full verdict before you commit.
        </>
      ),
    },
    {
      icon: <ReportIcon />,
      title: "Read the verdict",
      description: (
        <>
          <Cmd>sentry report</Cmd> shows the latest report with the five
          coverage dimensions and evidence for each finding.
        </>
      ),
    },
    {
      icon: <HistoryIcon />,
      title: "Compare history",
      description: (
        <>
          <Cmd>sentry history</Cmd> lists runs and compares the last two:
          coverage, tests and findings side by side.
        </>
      ),
    },
    {
      icon: <ArchiveIcon />,
      title: "Archive the evidence",
      description: (
        <>
          <Cmd>sentry archive</Cmd> versions screenshot, video and verdict per
          module, either by certified specs or by a truly photographed route.
        </>
      ),
    },
    {
      icon: <IssueIcon />,
      title: "See the whole application",
      description: (
        <>
          <Cmd>sentry status</Cmd> measures everything against every declared
          spec, always via the full suite: the periodic snapshot, not the
          day-to-day loop.
        </>
      ),
    },
  ],
};

const firstStepsByLang: Record<"pt" | "en", Card[]> = {
  pt: [
    {
      icon: <DownloadIcon />,
      title: "Instalação",
      description: (
        <>
          <Cmd>pip install sentry-test</Cmd>. Requer Python 3.11+; confirme com{" "}
          <Cmd>sentry --version</Cmd>.
        </>
      ),
    },
    {
      icon: <SlidersIcon />,
      title: "Setup",
      description: (
        <>
          <Cmd>sentry init [--install]</Cmd> prepara o repositório e escreve o
          fluxo para o seu agente de IA.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      title: "O fluxo de trabalho",
      description:
        "Os seis passos: declarar, preencher, validar, ligar ao teste, rodar e comparar histórico.",
    },
    {
      icon: <TerminalIcon />,
      title: "Comandos e Habilidades",
      description: (
        <>
          Referência completa de{" "}
          <span className="text-[var(--text-h)]">init</span>,{" "}
          <span className="text-[var(--text-h)]">new</span>,{" "}
          <span className="text-[var(--text-h)]">check</span>,{" "}
          <span className="text-[var(--text-h)]">run</span>,{" "}
          <span className="text-[var(--text-h)]">report</span>,{" "}
          <span className="text-[var(--text-h)]">history</span>,{" "}
          <span className="text-[var(--text-h)]">archive</span> e{" "}
          <span className="text-[var(--text-h)]">clear</span>.
        </>
      ),
    },
  ],
  en: [
    {
      icon: <DownloadIcon />,
      title: "Installation",
      description: (
        <>
          <Cmd>pip install sentry-test</Cmd>. Requires Python 3.11+; confirm
          with <Cmd>sentry --version</Cmd>.
        </>
      ),
    },
    {
      icon: <SlidersIcon />,
      title: "Setup",
      description: (
        <>
          <Cmd>sentry init [--install]</Cmd> prepares the repository and writes
          the flow for your AI agent.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      title: "The workflow",
      description:
        "Six steps: declare, fill in, validate, link to test, run and compare history.",
    },
    {
      icon: <TerminalIcon />,
      title: "Commands & Skills",
      description: (
        <>
          Full reference for <span className="text-[var(--text-h)]">init</span>,{" "}
          <span className="text-[var(--text-h)]">new</span>,{" "}
          <span className="text-[var(--text-h)]">check</span>,{" "}
          <span className="text-[var(--text-h)]">run</span>,{" "}
          <span className="text-[var(--text-h)]">report</span>,{" "}
          <span className="text-[var(--text-h)]">history</span>,{" "}
          <span className="text-[var(--text-h)]">archive</span> and{" "}
          <span className="text-[var(--text-h)]">clear</span>.
        </>
      ),
    },
  ],
};

const learnMoreByLang: Record<"pt" | "en", Card[]> = {
  pt: [
    {
      icon: <BranchIcon />,
      title: "Repositório",
      description: "Leia o código-fonte, veja o histórico e dê uma estrela no GitHub.",
      href: "https://github.com/lucasnicolau30/sentry",
      external: true,
    },
    {
      icon: <PackageIcon />,
      title: "Pacote PyPI",
      description: (
        <>
          Instale o <span className="text-[var(--text-h)]">sentry-test</span>{" "}
          direto do índice do PyPI.
        </>
      ),
      href: "https://pypi.org/project/sentry-test/",
      external: true,
    },
    {
      icon: <IssueIcon />,
      title: "Reporte um problema",
      description:
        "Encontrou um bug ou tem uma ideia? Abra uma issue no GitHub.",
      href: "https://github.com/lucasnicolau30/sentry/issues",
      external: true,
    },
  ],
  en: [
    {
      icon: <BranchIcon />,
      title: "Repository",
      description: "Read the source, follow the history and star it on GitHub.",
      href: "https://github.com/lucasnicolau30/sentry",
      external: true,
    },
    {
      icon: <PackageIcon />,
      title: "PyPI package",
      description: (
        <>
          Install <span className="text-[var(--text-h)]">sentry-test</span>{" "}
          straight from the PyPI index.
        </>
      ),
      href: "https://pypi.org/project/sentry-test/",
      external: true,
    },
    {
      icon: <IssueIcon />,
      title: "Report an issue",
      description: "Found a bug or have an idea? Open an issue on GitHub.",
      href: "https://github.com/lucasnicolau30/sentry/issues",
      external: true,
    },
  ],
};

function GetStartedContent({ onNextClick }: { onNextClick: () => void }) {
  const { lang, t } = useLanguage();

  return (
    <div className="mx-auto max-w-5xl px-6 py-14">
      <Reveal>
        <h2 className="text-xl font-semibold text-[var(--text-h)]">
          {t("O que é o Sentry?", "What is Sentry?")}
        </h2>
        <p className="mt-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
          {lang === "pt" ? (
            <>
              O <span className="text-[var(--text-h)]">Sentry</span> é uma CLI
              de qualidade de teste orientada a mudança. O agente de IA declara
              a intenção em markdown; o{" "}
              <span className="text-[var(--text-h)]">Sentry</span> mede a
              realidade: roda a suíte, lê o diff e a cobertura, e emite um
              veredito auditável.
            </>
          ) : (
            <>
              <span className="text-[var(--text-h)]">Sentry</span> is a
              change-oriented test quality CLI. The AI agent declares intent in
              markdown; <span className="text-[var(--text-h)]">Sentry</span>{" "}
              measures reality: it runs the suite, reads the diff and coverage,
              and issues an auditable verdict.
            </>
          )}
        </p>

        <div className="mx-auto mt-5 max-w-lg">
          <TerminalWindow title="tree">
            <p className="text-[var(--text-h)]">.sentry/</p>
            <p className="text-[var(--text)]/70">├── specs/</p>
            <p className="text-[var(--text)]/70">
              │&nbsp;&nbsp;&nbsp;&nbsp;└──{" "}
              {t("cadastro-de-cliente", "customer-registration")}/
            </p>
            <p className="text-[var(--text-h)]">
              │&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── PROMPT.md
            </p>
            <p className="text-[var(--text-h)]">
              │&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── CASES.md
            </p>
            <p className="text-[var(--text)]/70">├── storage/</p>
            <p className="text-[var(--text)]/70">
              │&nbsp;&nbsp;&nbsp;&nbsp;└──{" "}
              {t("cadastro-de-cliente", "customer-registration")}-1.0.0/
            </p>
            <p className="text-[var(--text-h)]">
              │&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── README.md
            </p>
            <p className="text-[var(--text-h)]">
              │&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── media/
            </p>
            <p className="text-[var(--text)]/70">└── reports/</p>
            <p className="text-[var(--text-h)]">
              &nbsp;&nbsp;&nbsp;&nbsp;└── latest-&lt;data&gt;.md
            </p>
          </TerminalWindow>
        </div>
      </Reveal>

      <Reveal>
        <h2 className="mt-14 text-xl font-semibold text-[var(--text-h)]">
          {t("Princípios do Sentry", "Sentry's principles")}
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {principlesByLang[lang].map((card) => (
            <DocCard key={String(card.title)} {...card} />
          ))}
        </div>
      </Reveal>

      <Reveal>
        <h2 className="mt-14 text-xl font-semibold text-[var(--text-h)]">
          {t("O que você pode fazer", "What you can do")}
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {actionsByLang[lang].map((card, index) => (
            <DocCard
              key={String(card.title)}
              {...card}
              className={index === actionsByLang[lang].length - 1 ? "lg:col-span-2" : ""}
            />
          ))}
        </div>
      </Reveal>

      <Reveal>
        <h2 className="mt-14 text-xl font-semibold text-[var(--text-h)]">
          {t("Primeiros passos", "First steps")}
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {firstStepsByLang[lang].map((card) => (
            <DocCard key={String(card.title)} {...card} />
          ))}
        </div>
      </Reveal>

      <Reveal>
        <h2 className="mt-14 text-xl font-semibold text-[var(--text-h)]">
          {t("Saiba mais sobre o Sentry", "Learn more about Sentry")}
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {learnMoreByLang[lang].map((card) => (
            <DocCard key={String(card.title)} {...card} />
          ))}
        </div>
      </Reveal>

      <PageFooter
        nextLabel={t("Setup e configuração", "Setup & configuration")}
        onNextClick={onNextClick}
        className="mt-14"
      />
    </div>
  );
}

const setupSectionsByLang = {
  pt: [
    { id: "prepare-o-ambiente", label: "Prepare o ambiente" },
    { id: "instale-a-cli", label: "Instale a CLI" },
    { id: "inicialize-o-repositorio", label: "Inicialize o repositório" },
    { id: "dependencias", label: "Dependências ausentes" },
    { id: "sentry-toml", label: "Configure o sentry.toml" },
    { id: "stacks-suportadas", label: "Stacks suportadas" },
    { id: "gitignore", label: "O que fica versionado" },
  ],
  en: [
    { id: "prepare-o-ambiente", label: "Prepare the environment" },
    { id: "instale-a-cli", label: "Install the CLI" },
    { id: "inicialize-o-repositorio", label: "Initialize the repository" },
    { id: "dependencias", label: "Missing dependencies" },
    { id: "sentry-toml", label: "Configure sentry.toml" },
    { id: "stacks-suportadas", label: "Supported stacks" },
    { id: "gitignore", label: "What gets versioned" },
  ],
};

const stacksSupportByLang = {
  pt: [
    {
      capability: "Execução da suíte",
      support:
        "qualquer comando com saída JUnit XML: pytest, Jest, Vitest, go test (gotestsum), Surefire, dotnet test, RSpec, PHPUnit",
    },
    {
      capability: "Cobertura",
      support:
        "lcov (nyc, c8, Jest, simplecov), Cobertura XML (JaCoCo, coverlet), coverage.py (JSON), detectados pelo conteúdo",
    },
    {
      capability: "Rastreabilidade caso↔teste",
      support:
        ".py, .js/.jsx/.ts/.tsx, .go, .java/.kt, .cs, .rb, .php, .rs; marcador cenario: funciona em qualquer comentário",
    },
    {
      capability: "Caminhos de erro",
      support:
        "por AST em Python; por padrão sintático (throw, catch, panic, rescue, panic!) nas demais linguagens",
    },
  ],
  en: [
    {
      capability: "Suite execution",
      support:
        "any command with JUnit XML output: pytest, Jest, Vitest, go test (gotestsum), Surefire, dotnet test, RSpec, PHPUnit",
    },
    {
      capability: "Coverage",
      support:
        "lcov (nyc, c8, Jest, simplecov), Cobertura XML (JaCoCo, coverlet), coverage.py (JSON), detected by content",
    },
    {
      capability: "Case↔test traceability",
      support:
        ".py, .js/.jsx/.ts/.tsx, .go, .java/.kt, .cs, .rb, .php, .rs; the scenario: marker works in any comment",
    },
    {
      capability: "Error paths",
      support:
        "via AST in Python; via syntactic pattern (throw, catch, panic, rescue, panic!) in other languages",
    },
  ],
};

function SetupContent({
  onPrevClick,
  onNextClick,
}: {
  onPrevClick: () => void;
  onNextClick: () => void;
}) {
  const { lang, t } = useLanguage();
  const stacksSupport = stacksSupportByLang[lang];

  return (
    <div className="mx-auto max-w-5xl px-6 pb-14 pt-6">
      <div className="flex gap-8 lg:gap-12">
        <div className="min-w-0 flex-1">
          <Reveal>
            <h1 className="text-3xl font-semibold uppercase tracking-normal text-[var(--text-h)]">
              {t("Setup e configuração", "Setup & configuration")}
            </h1>
            {lang === "pt" ? (
              <p className="mt-6 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Três comandos preparam o repositório para o ciclo intenção →
                veredito: instalar a CLI, rodar{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> sentry init
                </span>{" "}
                e, se quiser, ajustar o{" "}
                <span className="text-[var(--text-h)]">sentry.toml</span>. Nada
                disso é destrutivo:{" "}
                <span className="text-[var(--text-h)]">init</span> é idempotente
                e nunca sobrescreve configuração existente.
              </p>
            ) : (
              <p className="mt-6 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Three commands prepare the repository for the intent → verdict
                cycle: install the CLI, run{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> sentry init
                </span>{" "}
                and, if you want, tweak{" "}
                <span className="text-[var(--text-h)]">sentry.toml</span>. None
                of it is destructive:{" "}
                <span className="text-[var(--text-h)]">init</span> is idempotent
                and never overwrites existing configuration.
              </p>
            )}
          </Reveal>

          <Reveal>
            <h2
              id="prepare-o-ambiente"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Prepare o ambiente", "Prepare the environment")}
            </h2>
            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  Quase todo mundo já tem Python instalado, mas vale confirmar a
                  versão antes de seguir, pois o{" "}
                  <span className="text-[var(--text-h)]">Sentry</span> requer
                  3.11+:
                </>
              ) : (
                <>
                  Almost everyone already has Python installed, but it's worth
                  confirming the version before moving on, since{" "}
                  <span className="text-[var(--text-h)]">Sentry</span> requires
                  3.11+:
                </>
              )}
            </p>
            <CodeBlock lines={["python --version", "Python 3.11.0"]} />
            <p className="mb-3 mt-4 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                "Se a versão for menor que 3.11 ou o comando não existir, instale uma versão atual antes de continuar. Um ambiente virtual isolado por projeto evita conflito entre dependências de projetos diferentes; não é obrigatório, mas é uma boa prática:",
                "If the version is below 3.11 or the command doesn't exist, install a current version before continuing. A per-project virtual environment avoids dependency conflicts between different projects; not required, but a good practice:",
              )}
            </p>
            <CodeBlock
              lines={["python -m venv .venv", "source .venv/bin/activate"]}
            />
          </Reveal>

          <Reveal>
            <h2
              id="instale-a-cli"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Instale a CLI", "Install the CLI")}
            </h2>
            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                "Com o ambiente pronto, instale via pip e confirme a versão do pacote:",
                "With the environment ready, install via pip and confirm the package version:",
              )}
            </p>
            <CodeBlock lines={["pip install sentry-test"]} />
            <div className="mt-3">
              <CodeBlock lines={["sentry --version", "sentry-test x.y.z"]} />
            </div>
          </Reveal>

          <Reveal>
            <h2
              id="inicialize-o-repositorio"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Inicialize o repositório", "Initialize the repository")}
            </h2>
            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Dentro do seu projeto, rode{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> sentry init
                </span>
                . Ele cria a pasta{" "}
                <span className="text-[var(--text-h)]">.sentry/</span> (specs,
                execuções, relatórios e banco), o{" "}
                <span className="text-[var(--text-h)]">sentry.toml</span>, as
                entradas do{" "}
                <span className="text-[var(--text-h)]">.gitignore</span> e
                escreve o fluxo para o seu agente de IA em dois lugares: a skill{" "}
                <span className="text-[var(--text-h)]">sentry-cases</span>{" "}
                (Claude Code) e o{" "}
                <span className="text-[var(--text-h)]">AGENT-SENTRY.md</span> na
                raiz, para outros agentes.
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Inside your project, run{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> sentry init
                </span>
                . It creates the{" "}
                <span className="text-[var(--text-h)]">.sentry/</span> folder
                (specs, runs, reports and database), the{" "}
                <span className="text-[var(--text-h)]">sentry.toml</span>, the{" "}
                <span className="text-[var(--text-h)]">.gitignore</span>{" "}
                entries, and writes the flow for your AI agent in two places:
                the <span className="text-[var(--text-h)]">sentry-cases</span>{" "}
                skill (Claude Code) and{" "}
                <span className="text-[var(--text-h)]">AGENT-SENTRY.md</span> at
                the root, for other agents.
              </p>
            )}
            <CodeBlock lines={["cd your-project", "sentry init"]} />
          </Reveal>

          <Reveal>
            <h2
              id="dependencias"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Dependências ausentes", "Missing dependencies")}
            </h2>
            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Se faltar <span className="text-[var(--text-h)]">pytest</span>{" "}
                ou <span className="text-[var(--text-h)]">coverage</span>, o{" "}
                <span className="text-[var(--text-h)]">init</span> avisa em vez
                de falhar. Para instalar junto, use a flag{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> --install
                </span>
                :
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                If <span className="text-[var(--text-h)]">pytest</span> or{" "}
                <span className="text-[var(--text-h)]">coverage</span> are
                missing, <span className="text-[var(--text-h)]">init</span>{" "}
                warns instead of failing. To install them too, use the{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> --install
                </span>{" "}
                flag:
              </p>
            )}
            <CodeBlock lines={["sentry init --install"]} />
          </Reveal>

          <Reveal>
            <h2
              id="sentry-toml"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Configure o sentry.toml", "Configure sentry.toml")}
            </h2>
            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  Fica na raiz, é versionável e sem segredos. Tudo além do que o{" "}
                  <span className="text-[var(--text-h)]">init</span> já escreve
                  é opcional; ajuste só o que o seu projeto precisa:
                </>
              ) : (
                <>
                  Lives at the root, is versionable and holds no secrets.
                  Everything beyond what{" "}
                  <span className="text-[var(--text-h)]">init</span> already
                  writes is optional; adjust only what your project needs:
                </>
              )}
            </p>
            <TerminalWindow title="sentry.toml">
              <p className="text-[var(--text-h)]">[project]</p>
              <p className="pl-2">
                name ={" "}
                <span className="text-[var(--accent)]">
                  {t('"meu-projeto"', '"my-project"')}
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[specs]</p>
              <p className="pl-2">
                path ={" "}
                <span className="text-[var(--accent)]">".sentry/specs"</span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[test]</p>
              <p className="pl-2">
                command ={" "}
                <span className="text-[var(--accent)]">"npx jest"</span>{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "qualquer executor com saída JUnit XML",
                    "any runner that exports JUnit XML",
                  )}
                </span>
              </p>
              <p className="pl-2">
                junit_xml ={" "}
                <span className="text-[var(--accent)]">
                  "reports/junit.xml"
                </span>{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "sem isto, injeta --junitxml (pytest)",
                    "without this, injects --junitxml (pytest)",
                  )}
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[tests]</p>
              <p className="pl-2">
                paths = <span className="text-[var(--accent)]">["tests"]</span>{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "padrão: tests, test, spec, __tests__",
                    "default: tests, test, spec, __tests__",
                  )}
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[coverage]</p>
              <p className="pl-2">
                path ={" "}
                <span className="text-[var(--accent)]">
                  "coverage/lcov.info"
                </span>
              </p>
              <p className="pl-2">
                format = <span className="text-[var(--accent)]">"lcov"</span>{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "opcional: detectado pelo conteúdo",
                    "optional: detected by content",
                  )}
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">
                [e2e]{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "opcional: segunda suíte para casos de camada frontend",
                    "optional: second suite for frontend-layer cases",
                  )}
                </span>
              </p>
              <p className="pl-2">
                command ={" "}
                <span className="text-[var(--accent)]">
                  "npx playwright test --reporter=junit"
                </span>
              </p>
              <p className="pl-2">
                junit_xml ={" "}
                <span className="text-[var(--accent)]">
                  "frontend/reports/junit.xml"
                </span>
              </p>
              <p className="pl-2">
                paths ={" "}
                <span className="text-[var(--accent)]">["frontend/e2e"]</span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[analysis]</p>
              <p className="pl-2">
                run_tests_by_default ={" "}
                <span className="text-[var(--accent)]">false</span>
              </p>
              <p className="pl-2">
                timeout_seconds ={" "}
                <span className="text-[var(--accent)]">300</span>
              </p>
              <p className="pl-2">
                exclude ={" "}
                <span className="text-[var(--accent)]">["frontend/"]</span>{" "}
                <span className="text-[var(--text)]/40">
                  # {t("diretórios fora do escopo", "directories out of scope")}
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[policy.thresholds]</p>
              <p className="pl-2">
                changed_coverage ={" "}
                <span className="text-[var(--accent)]">85</span>
              </p>
              <p className="pl-2">
                global_coverage ={" "}
                <span className="text-[var(--accent)]">90</span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[policy.severities]</p>
              <p className="pl-2">
                coverage-missing ={" "}
                <span className="text-[var(--accent)]">"alta"</span>{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "sobrescreve a severidade de qualquer regra",
                    "overrides the severity of any rule",
                  )}
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[catalog.fields]</p>
              <p className="pl-2">
                matricula ={" "}
                <span className="text-[var(--accent)]">
                  ["vazio", "formato-invalido", "valida"]
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">[dimensions]</p>
              <p className="pl-2">
                disabled = <span className="text-[var(--accent)]">[]</span>{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "eixos que não se aplicam ao projeto",
                    "axes that don't apply to the project",
                  )}
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">
                [modules]{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "sentry archive por specs certificadas",
                    "sentry archive by certified specs",
                  )}
                </span>
              </p>
              <p className="pl-2">
                cadastro-de-cliente ={" "}
                <span className="text-[var(--accent)]">
                  ["cadastro-de-cliente"]
                </span>
              </p>
              <p className="mt-2 text-[var(--text-h)]">
                [modules.pagina-inicial]{" "}
                <span className="text-[var(--text)]/40">
                  #{" "}
                  {t(
                    "sentry archive por rota fotografada",
                    "sentry archive by photographed route",
                  )}
                </span>
              </p>
              <p className="pl-2">
                rotas = <span className="text-[var(--accent)]">["/", "/docs"]</span>
              </p>
            </TerminalWindow>
            <p className="mt-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  Sem limiar declarado em [policy.thresholds], o{" "}
                  <span className="text-[var(--text-h)]">Sentry</span> não
                  inventa um mínimo: quem define "quanto basta" é o projeto.
                </>
              ) : (
                <>
                  Without a threshold declared in [policy.thresholds],{" "}
                  <span className="text-[var(--text-h)]">Sentry</span> never
                  invents a minimum: the project decides what's "enough".
                </>
              )}
            </p>
          </Reveal>

          <Reveal>
            <h2
              id="stacks-suportadas"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Stacks suportadas", "Supported stacks")}
            </h2>
            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  A derivação, do pedido à matriz de casos, é agnóstica de
                  linguagem: o{" "}
                  <span className="text-[var(--text-h)]">CASES.md</span> é
                  markdown e o catálogo raciocina sobre tipo de dado, não sobre
                  código. A verificação depende do formato de intercâmbio que
                  sua suíte exporta, não da ferramenta:
                </>
              ) : (
                <>
                  Derivation, from request to case matrix, is
                  language-agnostic:{" "}
                  <span className="text-[var(--text-h)]">CASES.md</span> is
                  markdown and the catalog reasons about data type, not code.
                  Verification depends on the exchange format your suite
                  exports, not on the tool:
                </>
              )}
            </p>
            <div className="overflow-hidden rounded-xl border border-[var(--border)] transition-transform duration-300 hover:-translate-y-1">
              {stacksSupport.map((item, index) => (
                <div
                  key={item.capability}
                  className={`bg-[var(--bg-alt)] px-5 py-3 ${index < stacksSupport.length - 1 ? "border-b border-[var(--border)]" : ""}`}
                >
                  <p className="text-base font-semibold text-[var(--text-h)]">
                    {item.capability}
                  </p>
                  <p className="mt-1 text-justify text-base leading-relaxed text-[var(--text)]/70">
                    {item.support}
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  Camada <span className="text-[var(--text-h)]">frontend</span>{" "}
                  é verificada por uma segunda suíte, declarada em{" "}
                  <span className="text-[var(--text-h)]">[e2e]</span>; o
                  reporter JUnit do Playwright encaixa nativamente. Seus casos
                  nunca ganham cobertura de linha: o status vem de evidência de
                  execução (o cenário rodou e passou, trace/screenshot anexado),
                  nunca de um número de cobertura.
                </>
              ) : (
                <>
                  The <span className="text-[var(--text-h)]">frontend</span>{" "}
                  layer is verified by a second suite, declared under{" "}
                  <span className="text-[var(--text-h)]">[e2e]</span>;
                  Playwright's JUnit reporter is a native fit. Its cases never
                  get line coverage: status comes from execution evidence (the
                  scenario ran and passed, trace/screenshot attached), never
                  from a coverage number.
                </>
              )}
            </p>
          </Reveal>

          <Reveal>
            <h2
              id="gitignore"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("O que fica versionado", "What gets versioned")}
            </h2>
            <p className="text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  A evidência gerada (execuções, banco e relatórios) fica fora
                  do Git, com duas exceções deliberadas:{" "}
                  <span className="text-[var(--text-h)]">
                    .sentry/reports/latest-&lt;data&gt;.md
                  </span>{" "}
                  é versionado, para o veredito aparecer no diff sem que quem lê
                  precise rodar o{" "}
                  <span className="text-[var(--text-h)]">Sentry</span>, e{" "}
                  <span className="text-[var(--text-h)]">.sentry/storage/</span>{" "}
                  também, porque é ali que{" "}
                  <span className="text-[var(--text-h)]">sentry archive</span>{" "}
                  versiona print, vídeo e veredito por módulo. As specs em{" "}
                  <span className="text-[var(--text-h)]">.sentry/specs/</span>{" "}
                  são versionadas e nunca removidas: são intenção declarada, não
                  evidência gerada. Sem elas no repositório, um checkout limpo
                  não tem matriz de casos e a análise sai inconclusiva por falta
                  de spec, em vez de medir.
                </>
              ) : (
                <>
                  Generated evidence (runs, database and reports) stays out of
                  Git, with two deliberate exceptions:{" "}
                  <span className="text-[var(--text-h)]">
                    .sentry/reports/latest-&lt;date&gt;.md
                  </span>{" "}
                  is versioned, so the verdict shows up in the diff without the
                  reader having to run{" "}
                  <span className="text-[var(--text-h)]">Sentry</span>, and{" "}
                  <span className="text-[var(--text-h)]">.sentry/storage/</span>{" "}
                  too, since that's where{" "}
                  <span className="text-[var(--text-h)]">sentry archive</span>{" "}
                  versions screenshot, video and verdict per module. Specs in{" "}
                  <span className="text-[var(--text-h)]">.sentry/specs/</span>{" "}
                  are versioned and never removed: they're declared intent, not
                  generated evidence. Without them in the repository, a clean
                  checkout has no case matrix and the analysis comes back
                  inconclusive for lack of a spec instead of measuring.
                </>
              )}
            </p>
          </Reveal>

          <PageFooter
            prevLabel={t("Comece aqui", "Getting started")}
            onPrevClick={onPrevClick}
            nextLabel={t("O fluxo de trabalho", "The workflow")}
            onNextClick={onNextClick}
            className="mt-14"
          />
        </div>

        <DocsSidebar
          sections={setupSectionsByLang[lang]}
          label={t("Nesta página", "On this page")}
        />
      </div>
    </div>
  );
}

const workflowSectionsByLang = {
  pt: [
    { id: "declare-a-intencao", label: "1. Declare a intenção" },
    { id: "preencha-com-o-agente", label: "2. Preencha com o agente" },
    { id: "valide-a-estrutura", label: "3. Valide a estrutura" },
    { id: "ligue-caso-a-teste", label: "4. Ligue caso a teste" },
    { id: "rode-e-persista", label: "5. Rode e persista" },
    { id: "releia-e-compare", label: "6. Releia e compare" },
  ],
  en: [
    { id: "declare-a-intencao", label: "1. Declare intent" },
    { id: "preencha-com-o-agente", label: "2. Fill in with the agent" },
    { id: "valide-a-estrutura", label: "3. Validate the structure" },
    { id: "ligue-caso-a-teste", label: "4. Link case to test" },
    { id: "rode-e-persista", label: "5. Run and persist" },
    { id: "releia-e-compare", label: "6. Read back and compare" },
  ],
};

const coverageDimensionsByLang = {
  pt: [
    {
      dimension: "Requisitos e regras de negócio",
      evidence: "cenários da spec com teste associado",
    },
    {
      dimension: "APIs, persistência, transações e integrações",
      evidence: "casos de tipo contrato/integração e camada integração",
    },
    {
      dimension: "Exceções, resiliência e recuperação",
      evidence: "caminhos de erro alterados executados por algum teste",
    },
    {
      dimension: "Segurança e autorização",
      evidence: "campos de tipo rota com todas as classes de acesso cobertas",
    },
    {
      dimension: "Interface e fluxo de usuário",
      evidence: "casos de camada frontend com evidência de execução e2e",
    },
  ],
  en: [
    {
      dimension: "Requirements and business rules",
      evidence: "spec scenarios with an associated test",
    },
    {
      dimension: "APIs, persistence, transactions and integrations",
      evidence: "contract/integration-type cases and integration layer",
    },
    {
      dimension: "Exceptions, resilience and recovery",
      evidence: "changed error paths executed by some test",
    },
    {
      dimension: "Security and authorization",
      evidence: "route-type fields with all access classes covered",
    },
    {
      dimension: "Interface and user flow",
      evidence: "frontend-layer cases with e2e execution evidence",
    },
  ],
};

function WorkflowContent({
  onPrevClick,
  onNextClick,
}: {
  onPrevClick: () => void;
  onNextClick: () => void;
}) {
  const { lang, t } = useLanguage();
  const coverageDimensions = coverageDimensionsByLang[lang];

  return (
    <div className="mx-auto max-w-5xl px-6 pb-14 pt-6">
      <div className="flex gap-8 lg:gap-12">
        <div className="min-w-0 flex-1">
          <Reveal>
            <h1 className="text-3xl font-semibold uppercase tracking-normal text-[var(--text-h)]">
              {t("O fluxo de trabalho", "The workflow")}
            </h1>
            <p className="mt-6 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                "Seis passos entre o pedido em texto livre e o veredito auditável. Todo passo também funciona sem agente, pelos comandos abaixo; o agente só automatiza a parte de redação.",
                "Six steps between the free-text request and the auditable verdict. Every step also works without an agent, via the commands below; the agent just automates the writing part.",
              )}
            </p>
          </Reveal>

          <Reveal>
            <h2
              id="declare-a-intencao"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("1. Declare a intenção", "1. Declare intent")}
            </h2>
            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Cria{" "}
                <span className="text-[var(--text-h)]">
                  .sentry/specs/&lt;slug&gt;/
                </span>{" "}
                com o <span className="text-[var(--text-h)]">PROMPT.md</span>{" "}
                (pedido preservado) e o{" "}
                <span className="text-[var(--text-h)]">CASES.md</span> em
                branco.
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Creates{" "}
                <span className="text-[var(--text-h)]">
                  .sentry/specs/&lt;slug&gt;/
                </span>{" "}
                with <span className="text-[var(--text-h)]">PROMPT.md</span>{" "}
                (the request preserved) and a blank{" "}
                <span className="text-[var(--text-h)]">CASES.md</span>.
              </p>
            )}
            <CodeBlock
              lines={[
                t(
                  'sentry new "cadastro de cliente"',
                  'sentry new "customer registration"',
                ),
              ]}
            />
          </Reveal>

          <Reveal>
            <h2
              id="preencha-com-o-agente"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("2. Preencha com o agente", "2. Fill in with the agent")}
            </h2>
            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                A skill{" "}
                <span className="text-[var(--text-h)]">sentry-cases</span>{" "}
                pergunta o que estiver ambíguo antes de escrever, e preenche o{" "}
                <span className="text-[var(--text-h)]">CASES.md</span> seguindo
                o template. O agente declara requisito, camada, tipo,
                prioridade, entrada e resultado esperado, nunca o status: quem
                mede a realidade é o{" "}
                <span className="text-[var(--text-h)]">Sentry</span>.
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                The <span className="text-[var(--text-h)]">sentry-cases</span>{" "}
                skill asks about anything ambiguous before writing, and fills in{" "}
                <span className="text-[var(--text-h)]">CASES.md</span> following
                the template. The agent declares requirement, layer, type,
                priority, input and expected result, never status:{" "}
                <span className="text-[var(--text-h)]">Sentry</span> is the one
                measuring reality.
              </p>
            )}
            <TerminalWindow title="CASES.md">
              <p className="text-[var(--text)]/40"># CASES.md</p>
              <p className="mt-2 text-[var(--text-h)]">
                ## {t("Cadastro de cliente", "Customer registration")}
              </p>
              <p className="mt-2 text-[var(--text)]/70">
                - **{t("requisito", "requirement")}**:{" "}
                {t("validar CPF antes de salvar", "validate CPF before saving")}
              </p>
              <p className="text-[var(--text)]/70">
                - **{t("camada", "layer")}**: backend
              </p>
              <p className="text-[var(--text)]/70">
                - **{t("tipo", "type")}**: {t("unitário", "unit")}
              </p>
              <p className="text-[var(--text)]/70">
                - **{t("classe", "class")}**: cpf
              </p>
              <p className="text-[var(--text)]/70">
                - **{t("prioridade", "priority")}**: {t("alta", "high")}
              </p>
              <p className="text-[var(--text)]/70">
                - **{t("entrada", "input")}**:{" "}
                {t(
                  "CPF com dígito verificador inválido",
                  "CPF with invalid check digit",
                )}
              </p>
              <p className="text-[var(--text)]/70">
                - **{t("resultado esperado", "expected result")}**:{" "}
                {t(
                  "rejeita com erro de validação",
                  "rejects with a validation error",
                )}
              </p>
            </TerminalWindow>
          </Reveal>

          <Reveal>
            <h2
              id="valide-a-estrutura"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("3. Valide a estrutura", "3. Validate the structure")}
            </h2>
            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                "Confere vocabulário, estrutura e a cobrança das classes de equivalência do catálogo antes de rodar qualquer teste:",
                "Checks vocabulary, structure and required catalog equivalence classes before running any test:",
              )}
            </p>
            <CodeBlock
              lines={[
                t(
                  "sentry check cadastro-de-cliente",
                  "sentry check customer-registration",
                ),
              ]}
            />

            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                O catálogo é uma tabela fixa de situações que precisam de teste,
                por tipo de campo; não gera casos, cobra os que o agente deixou
                de declarar. Tipos conhecidos:{" "}
                <span className="text-[var(--text-h)]">cpf</span>,{" "}
                <span className="text-[var(--text-h)]">cnpj</span>,{" "}
                <span className="text-[var(--text-h)]">email</span>,{" "}
                <span className="text-[var(--text-h)]">senha</span>,{" "}
                <span className="text-[var(--text-h)]">data</span>,{" "}
                <span className="text-[var(--text-h)]">telefone</span>,{" "}
                <span className="text-[var(--text-h)]">cep</span>,{" "}
                <span className="text-[var(--text-h)]">inteiro</span>,{" "}
                <span className="text-[var(--text-h)]">decimal</span>,{" "}
                <span className="text-[var(--text-h)]">texto</span>,{" "}
                <span className="text-[var(--text-h)]">rota</span>,{" "}
                <span className="text-[var(--text-h)]">formulario</span>,{" "}
                <span className="text-[var(--text-h)]">navegacao</span>,{" "}
                <span className="text-[var(--text-h)]">responsivo</span> e{" "}
                <span className="text-[var(--text-h)]">acessibilidade</span>,
                sendo que os quatro últimos são para casos de camada{" "}
                <span className="text-[var(--text-h)]">frontend</span>,
                verificados por evidência de execução do Playwright. Uma classe
                que não faz sentido pode ser dispensada com justificativa em vez
                de virar caso artificial:
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                The catalog is a fixed table of situations that need a test, per
                field type; it doesn't generate cases, it charges for the ones
                the agent left undeclared. Known types:{" "}
                <span className="text-[var(--text-h)]">cpf</span>,{" "}
                <span className="text-[var(--text-h)]">cnpj</span>,{" "}
                <span className="text-[var(--text-h)]">email</span>,{" "}
                <span className="text-[var(--text-h)]">password</span>,{" "}
                <span className="text-[var(--text-h)]">date</span>,{" "}
                <span className="text-[var(--text-h)]">phone</span>,{" "}
                <span className="text-[var(--text-h)]">zip</span>,{" "}
                <span className="text-[var(--text-h)]">integer</span>,{" "}
                <span className="text-[var(--text-h)]">decimal</span>,{" "}
                <span className="text-[var(--text-h)]">text</span>,{" "}
                <span className="text-[var(--text-h)]">route</span>,{" "}
                <span className="text-[var(--text-h)]">formulario</span> (form),{" "}
                <span className="text-[var(--text-h)]">navegacao</span>{" "}
                (navigation),{" "}
                <span className="text-[var(--text-h)]">responsivo</span>{" "}
                (responsive) and{" "}
                <span className="text-[var(--text-h)]">acessibilidade</span>{" "}
                (accessibility), and the last four are for
                <span className="text-[var(--text-h)]"> frontend</span>-layer
                cases, verified by Playwright execution evidence. A class that
                doesn't make sense can be waived with justification instead of
                turning into an artificial case:
              </p>
            )}
            <TerminalWindow title="CASES.md">
              <p className="text-[var(--text-h)]">
                ## {t("Classes não aplicáveis", "Non-applicable classes")}
              </p>
              <p className="mt-1 text-[var(--text)]/70">
                -{" "}
                <span className="text-[var(--text-h)]">
                  exclude/max-length-exceeded
                </span>
                :{" "}
                {t(
                  "é parâmetro de configuração, não campo de formulário",
                  "it's a configuration parameter, not a form field",
                )}
              </p>
            </TerminalWindow>

            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                "A cobertura é medida em cinco dimensões, cada uma reportando coberta, parcial, não coberta ou não aplicável, com evidência:",
                "Coverage is measured across five dimensions, each reporting covered, partial, not covered or not applicable, with evidence:",
              )}
            </p>
            <div className="overflow-hidden rounded-xl border border-[var(--border)] transition-transform duration-300 hover:-translate-y-1">
              {coverageDimensions.map((item, index) => (
                <div
                  key={item.dimension}
                  className={`bg-[var(--bg-alt)] px-5 py-3 ${index < coverageDimensions.length - 1 ? "border-b border-[var(--border)]" : ""}`}
                >
                  <p className="text-base font-semibold text-[var(--text-h)]">
                    {item.dimension}
                  </p>
                  <p className="mt-1 text-justify text-base leading-relaxed text-[var(--text)]/70">
                    {item.evidence}
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                '"Não aplicável" é distinto de "não coberta": um projeto sem rotas não é punido na dimensão de segurança.',
                '"Not applicable" is different from "not covered": a project without routes isn\'t penalized on the security dimension.',
              )}
            </p>
          </Reveal>

          <Reveal>
            <h2
              id="ligue-caso-a-teste"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("4. Ligue caso a teste", "4. Link case to test")}
            </h2>
            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Seu agente liga cada caso do{" "}
                <span className="text-[var(--text-h)]">CASES.md</span> ao teste
                real com um marcador de comentário, com o nome exato do caso;
                funciona em qualquer linguagem com comentário:
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Your agent links each case in{" "}
                <span className="text-[var(--text-h)]">CASES.md</span> to the
                real test with a comment marker, using the case's exact name;
                works in any language that supports comments:
              </p>
            )}
            <TerminalWindow title="test_customer.py">
              <p className="text-[var(--text)]/40">
                # scenario:{" "}
                {t(
                  "cliente com CPF inválido é rejeitado",
                  "customer with invalid CPF is rejected",
                )}
              </p>
              <p className="text-[var(--text-h)]">
                def test_customer_invalid_cpf():
              </p>
              <p className="pl-4 text-[var(--text)]/60">...</p>
            </TerminalWindow>
          </Reveal>

          <Reveal>
            <h2
              id="rode-e-persista"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("5. Rode e persista", "5. Run and persist")}
            </h2>
            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Roda a suíte, lê diff e cobertura, aplica as dez regras
                determinísticas e persiste o resultado. Sem{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> --run-tests
                </span>{" "}
                não há cobertura, e o veredito tende a inconclusivo:
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Runs the suite, reads diff and coverage, applies the ten
                deterministic rules and persists the result. Without{" "}
                <span className="text-[var(--text-h)]">
                  <span className="text-[var(--accent)]">$</span> --run-tests
                </span>{" "}
                there's no coverage, and the verdict tends toward inconclusive:
              </p>
            )}
            <CodeBlock
              lines={[
                t(
                  "sentry run --spec cadastro-de-cliente --run-tests",
                  "sentry run --spec customer-registration --run-tests",
                ),
              ]}
            />
          </Reveal>

          <Reveal>
            <h2
              id="releia-e-compare"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("6. Releia e compare", "6. Read back and compare")}
            </h2>
            {lang === "pt" ? (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                <Cmd>report</Cmd> exibe o último relatório; <Cmd>history</Cmd>{" "}
                lista execuções e compara as duas últimas: cobertura, testes,
                achados novos, resolvidos e persistentes.
              </p>
            ) : (
              <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
                <Cmd>report</Cmd> shows the latest report; <Cmd>history</Cmd>{" "}
                lists runs and compares the last two: coverage, tests, new,
                resolved and persistent findings.
              </p>
            )}
            <div className="space-y-3">
              <CodeBlock lines={["sentry report"]} />
              <CodeBlock lines={["sentry history"]} />
            </div>
          </Reveal>

          <PageFooter
            prevLabel={t("Setup e configuração", "Setup & configuration")}
            onPrevClick={onPrevClick}
            nextLabel={t("Comandos e Habilidades", "Commands & Skills")}
            onNextClick={onNextClick}
            className="mt-14"
          />
        </div>

        <DocsSidebar
          sections={workflowSectionsByLang[lang]}
          label={t("Nesta página", "On this page")}
        />
      </div>
    </div>
  );
}

const TrashIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path
      d="M4 7h16M9 7V4h6v3M6 7l1 13a2 2 0 002 2h6a2 2 0 002-2l1-13"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

type Command = { icon: ReactNode; command: string; description: ReactNode };

const W = ({ children }: { children: ReactNode }) => (
  <span className="text-[var(--text-h)]">{children}</span>
);

const commandsRefByLang: Record<"pt" | "en", Command[]> = {
  pt: [
    {
      icon: <TerminalIcon />,
      command: "sentry init [--install]",
      description: (
        <>
          Prepara o repositório: <W>.sentry/</W>, <W>sentry.toml</W>,{" "}
          <W>.gitignore</W>, guia de agente e skills. Com <W>--install</W>,
          instala dependências ausentes.
        </>
      ),
    },
    {
      icon: <ScanIcon />,
      command: 'sentry new <nome> [--prompt "..."] [--json]',
      description: (
        <>
          Cria a pasta da spec com slug derivado do nome. <W>--json</W> emite
          template e vocabulário para o agente consumir.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      command: "sentry check [<slug>|all]",
      description: (
        <>
          Valida <W>CASES.md</W>: estrutura, vocabulário e cobrança de classes
          de equivalência. all valida todas as specs juntas.
        </>
      ),
    },
    {
      icon: <RunIcon />,
      command: "sentry run [--spec <slug>|all] [--run-tests]",
      description: (
        <>
          Executa a análise e persiste. Sem <W>--run-tests</W> não há cobertura,
          e o veredito tende a inconclusivo.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      command: "sentry review [--spec <slug>] [--base REF] [--no-tests]",
      description: (
        <>
          <W>check</W> + <W>run</W> + relatório num comando só, com testes por
          padrão. Ideal como hook de pre-commit local.
        </>
      ),
    },
    {
      icon: <ScanIcon />,
      command: "sentry watch",
      description: (
        <>
          Reavalia a cada salvamento, sem executar teste nem gastar token.
          Escala para a suíte completa quando o arquivo salvo é um teste.
        </>
      ),
    },
    {
      icon: <RunIcon />,
      command: "sentry context --json",
      description:
        "Emite as lacunas da última análise em JSON, para o agente de IA trabalhar só sobre o que falta.",
    },
    {
      icon: <HistoryIcon />,
      command: "sentry status [--json]",
      description: (
        <>
          Mede a aplicação inteira, não só o diff: todo arquivo tratado como
          alterado, sempre com a suíte completa e nunca do cache. Aponta
          arquivos com zero cobertura.
        </>
      ),
    },
    {
      icon: <ReportIcon />,
      command: "sentry report",
      description: (
        <>
          Exibe o último relatório (
          <W>.sentry/reports/latest-&lt;data&gt;.md</W>).
        </>
      ),
    },
    {
      icon: <HistoryIcon />,
      command: "sentry history",
      description:
        "Lista execuções e compara as duas últimas: cobertura, testes, achados novos, resolvidos e persistentes.",
    },
    {
      icon: <TrashIcon />,
      command: "sentry clear [--keep-last N] [--yes]",
      description: (
        <>
          Poda execuções e relatórios antigos. Sem <W>--yes</W> apenas mostra o
          que sairia. Nunca toca em <W>.sentry/specs/</W>.
        </>
      ),
    },
    {
      icon: <ArchiveIcon />,
      command:
        "sentry archive <modulo> --version X.Y.Z [--specs A,B,C] [--image] [--video]",
      description: (
        <>
          Executa a suíte e2e do módulo e, aprovada, arquiva a mídia em{" "}
          <W>.sentry/storage/&lt;modulo&gt;-&lt;versao&gt;/</W> com um{" "}
          <W>README.md</W> autossuficiente. Recusa veredito reprovado. A
          composição é declarada uma vez, com <W>--specs</W>, na versão 1.0.0.
          Sem <W>--image</W>/<W>--video</W>, tudo que for produzido é arquivado;
          pedindo uma das duas, só aquele tipo entra, e <W>--video</W> também
          liga a gravação de vídeo do Playwright.
        </>
      ),
    },
  ],
  en: [
    {
      icon: <TerminalIcon />,
      command: "sentry init [--install]",
      description: (
        <>
          Prepares the repository: <W>.sentry/</W>, <W>sentry.toml</W>,{" "}
          <W>.gitignore</W>, agent guide and skills. With <W>--install</W>,
          installs missing dependencies.
        </>
      ),
    },
    {
      icon: <ScanIcon />,
      command: 'sentry new <name> [--prompt "..."] [--json]',
      description: (
        <>
          Creates the spec folder with a slug derived from the name.{" "}
          <W>--json</W> emits a template and vocabulary for the agent to
          consume.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      command: "sentry check [<slug>|all]",
      description: (
        <>
          Validates <W>CASES.md</W>: structure, vocabulary and required
          equivalence classes. all validates every spec together.
        </>
      ),
    },
    {
      icon: <RunIcon />,
      command: "sentry run [--spec <slug>|all] [--run-tests]",
      description: (
        <>
          Runs the analysis and persists it. Without <W>--run-tests</W> there's
          no coverage, and the verdict tends toward inconclusive.
        </>
      ),
    },
    {
      icon: <FlowIcon />,
      command: "sentry review [--spec <slug>] [--base REF] [--no-tests]",
      description: (
        <>
          <W>check</W> + <W>run</W> + report in one command, with tests on by
          default. Ideal as a local pre-commit hook.
        </>
      ),
    },
    {
      icon: <ScanIcon />,
      command: "sentry watch",
      description: (
        <>
          Re-evaluates on every save, without running tests or spending tokens.
          Escalates to the full suite when the saved file is a test.
        </>
      ),
    },
    {
      icon: <RunIcon />,
      command: "sentry context --json",
      description:
        "Emits the last run's gaps as JSON, for the AI agent to work only over what's missing.",
    },
    {
      icon: <HistoryIcon />,
      command: "sentry status [--json]",
      description: (
        <>
          Measures the whole application, not just the diff: every file treated
          as changed, always with the full suite and never from the cache.
          Points out files with zero coverage.
        </>
      ),
    },
    {
      icon: <ReportIcon />,
      command: "sentry report",
      description: (
        <>
          Shows the latest report (<W>.sentry/reports/latest-&lt;date&gt;.md</W>
          ).
        </>
      ),
    },
    {
      icon: <HistoryIcon />,
      command: "sentry history",
      description:
        "Lists runs and compares the last two: coverage, tests, new, resolved and persistent findings.",
    },
    {
      icon: <TrashIcon />,
      command: "sentry clear [--keep-last N] [--yes]",
      description: (
        <>
          Prunes old runs and reports. Without <W>--yes</W> it only shows what
          would be removed. Never touches <W>.sentry/specs/</W>.
        </>
      ),
    },
    {
      icon: <ArchiveIcon />,
      command:
        "sentry archive <module> --version X.Y.Z [--specs A,B,C] [--image] [--video]",
      description: (
        <>
          Runs the module's e2e suite and, once approved, archives its media
          under <W>.sentry/storage/&lt;module&gt;-&lt;version&gt;/</W> with a
          self-contained <W>README.md</W>. Refuses a rejected verdict. The
          composition is declared once, with <W>--specs</W>, on version 1.0.0.
          Without <W>--image</W>/<W>--video</W>, everything produced is
          archived; with either, only that media type is kept, and{" "}
          <W>--video</W> also turns on Playwright's video recording.
        </>
      ),
    },
  ],
};

const exitCodesByLang = {
  pt: [
    { code: "0", label: "aprovado", tone: "text-[var(--accent)]" },
    {
      code: "1",
      label: "aprovado com ressalvas",
      tone: "text-[var(--text-h)]",
    },
    { code: "2", label: "reprovado", tone: "text-[#f87171]" },
    {
      code: "3",
      label: "inconclusivo ou erro de infraestrutura",
      tone: "text-[var(--text)]/60",
    },
  ],
  en: [
    { code: "0", label: "passed", tone: "text-[var(--accent)]" },
    { code: "1", label: "passed with warnings", tone: "text-[var(--text-h)]" },
    { code: "2", label: "failed", tone: "text-[#f87171]" },
    {
      code: "3",
      label: "inconclusive or infrastructure error",
      tone: "text-[var(--text)]/60",
    },
  ],
};

const commandsSectionsByLang = {
  pt: [
    { id: "referencia-de-comandos", label: "Referência de comandos" },
    { id: "codigos-de-saida", label: "Códigos de saída" },
    { id: "regras-deterministicas", label: "Regras determinísticas" },
    { id: "skill-sentry-cases", label: "Skill sentry-cases" },
  ],
  en: [
    { id: "referencia-de-comandos", label: "Command reference" },
    { id: "codigos-de-saida", label: "Exit codes" },
    { id: "regras-deterministicas", label: "Deterministic rules" },
    { id: "skill-sentry-cases", label: "sentry-cases skill" },
  ],
};

const deterministicRulesByLang = {
  pt: [
    {
      rule: "test-failing",
      severity: "crítica",
      tone: "text-[#f87171]",
      when: "a suíte tem teste falhando",
    },
    {
      rule: "case-spec-invalid",
      severity: "crítica",
      tone: "text-[#f87171]",
      when: (
        <>
          o <W>CASES.md</W> tem erro estrutural
        </>
      ),
    },
    {
      rule: "changed-code-uncovered",
      severity: "alta",
      tone: "text-[#fb923c]",
      when: "cobertura do código alterado é zero",
    },
    {
      rule: "scenario-without-test",
      severity: "alta",
      tone: "text-[#fb923c]",
      when: "caso declarado sem teste associado",
    },
    {
      rule: "error-path-without-test",
      severity: "alta",
      tone: "text-[#fb923c]",
      when: "raise/throw em linha alterada que nenhum teste executou",
    },
    {
      rule: "missing-equivalence-class",
      severity: "alta",
      tone: "text-[#fb923c]",
      when: "classe exigida pelo catálogo que nenhum caso cobre",
    },
    {
      rule: "coverage-below-threshold",
      severity: "alta",
      tone: "text-[#fb923c]",
      when: "cobertura do código alterado abaixo do limiar declarado",
    },
    {
      rule: "requirement-without-scenario",
      severity: "média",
      tone: "text-[#facc15]",
      when: "requisito sem cenário correspondente",
    },
    {
      rule: "coverage-missing",
      severity: "média",
      tone: "text-[#facc15]",
      when: "não foi possível calcular a cobertura do código alterado",
    },
    {
      rule: "global-coverage-below-threshold",
      severity: "média",
      tone: "text-[#facc15]",
      when: "cobertura global abaixo do limiar declarado",
    },
  ],
  en: [
    {
      rule: "test-failing",
      severity: "critical",
      tone: "text-[#f87171]",
      when: "the suite has a failing test",
    },
    {
      rule: "case-spec-invalid",
      severity: "critical",
      tone: "text-[#f87171]",
      when: (
        <>
          <W>CASES.md</W> has a structural error
        </>
      ),
    },
    {
      rule: "changed-code-uncovered",
      severity: "high",
      tone: "text-[#fb923c]",
      when: "coverage of the changed code is zero",
    },
    {
      rule: "scenario-without-test",
      severity: "high",
      tone: "text-[#fb923c]",
      when: "declared case has no associated test",
    },
    {
      rule: "error-path-without-test",
      severity: "high",
      tone: "text-[#fb923c]",
      when: "raise/throw on a changed line that no test executed",
    },
    {
      rule: "missing-equivalence-class",
      severity: "high",
      tone: "text-[#fb923c]",
      when: "catalog-required class that no case covers",
    },
    {
      rule: "coverage-below-threshold",
      severity: "high",
      tone: "text-[#fb923c]",
      when: "changed code coverage below the declared threshold",
    },
    {
      rule: "requirement-without-scenario",
      severity: "medium",
      tone: "text-[#facc15]",
      when: "requirement without a matching scenario",
    },
    {
      rule: "coverage-missing",
      severity: "medium",
      tone: "text-[#facc15]",
      when: "changed code coverage couldn't be calculated",
    },
    {
      rule: "global-coverage-below-threshold",
      severity: "medium",
      tone: "text-[#facc15]",
      when: "global coverage below the declared threshold",
    },
  ],
};

const ALL_COMMANDS = [
  "init",
  "new",
  "check",
  "run",
  "review",
  "watch",
  "status",
  "context",
  "report",
  "history",
  "archive",
  "clear",
];

function CommandsContent({
  onPrevClick,
  onNextClick,
}: {
  onPrevClick: () => void;
  onNextClick: () => void;
}) {
  const { lang, t } = useLanguage();
  const commandsRef = commandsRefByLang[lang];
  const exitCodes = exitCodesByLang[lang];
  const deterministicRules = deterministicRulesByLang[lang];

  return (
    <div className="mx-auto max-w-5xl px-6 pb-14 pt-6">
      <div className="flex gap-8 lg:gap-12">
        <div className="min-w-0 flex-1">
          <Reveal>
            <h1 className="text-3xl font-semibold uppercase tracking-normal text-[var(--text-h)]">
              {t("Comandos e Habilidades", "Commands & Skills")}
            </h1>
            <TextMarquee
              height={120}
              speed={0.7}
              className="mt-6 justify-center"
              prefix={
                <span className="whitespace-nowrap font-mono text-xl text-[var(--text)]/40 sm:text-2xl">
                  <span className="text-[var(--accent)]">$</span> sentry
                </span>
              }
            >
              {ALL_COMMANDS.map((command) => (
                <p
                  key={command}
                  className="flex h-11 items-center font-mono text-xl text-[var(--text-h)] sm:text-2xl"
                >
                  {command}
                </p>
              ))}
            </TextMarquee>
            <p className="mt-6 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  Doze comandos, um ciclo só: declarar intenção, validar
                  estrutura, rodar com cobertura, revisar antes de commitar,
                  reler o veredito, comparar histórico e arquivar evidência
                  versionada. Cada um tem página própria abaixo, com sintaxe
                  completa e o que muda em cada flag.
                </>
              ) : (
                <>
                  Twelve commands, one single cycle: declare intent, validate
                  structure, run with coverage, review before committing, read
                  back the verdict, compare history and archive versioned
                  evidence. Each one gets its own entry below, with full syntax
                  and what each flag changes.
                </>
              )}
            </p>
          </Reveal>

          <Reveal>
            <h2
              id="referencia-de-comandos"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Referência de comandos", "Command reference")}
            </h2>
            <div className="space-y-3">
              {commandsRef.map((item) => (
                <div
                  key={item.command}
                  className="glow-card rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] p-5 transition-colors duration-200 hover:border-[var(--accent)]/40"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 text-[var(--accent)]">
                      {item.icon}
                    </div>
                    <div className="min-w-0">
                      <code className="text-base text-[var(--text-h)]">
                        <span className="text-[var(--accent)]">$</span>{" "}
                        {item.command}
                      </code>
                      <p className="mt-1.5 text-justify text-base leading-relaxed text-[var(--text)]/70">
                        {item.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal>
            <h2
              id="codigos-de-saida"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Códigos de saída", "Exit codes")}
            </h2>
            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                'Quatro estados distinguíveis, para separar "código mal testado" de "meu ambiente quebrou". Erro de infraestrutura nunca produz veredito aprovado.',
                'Four distinguishable states, to separate "poorly tested code" from "my environment broke". An infrastructure error never produces a passing verdict.',
              )}
            </p>
            <div className="overflow-hidden rounded-xl border border-[var(--border)] transition-transform duration-300 hover:-translate-y-1">
              {exitCodes.map((item, index) => (
                <div
                  key={item.code}
                  className={`flex items-center gap-4 bg-[var(--bg-alt)] px-5 py-3 ${
                    index < exitCodes.length - 1
                      ? "border-b border-[var(--border)]"
                      : ""
                  }`}
                >
                  <code
                    className={`w-6 shrink-0 text-base font-semibold ${item.tone}`}
                  >
                    {item.code}
                  </code>
                  <span className="text-base text-[var(--text)]/80">
                    {item.label}
                  </span>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal>
            <h2
              id="regras-deterministicas"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Regras determinísticas", "Deterministic rules")}
            </h2>
            <p className="mb-3 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {t(
                "Dez regras, com severidade configurável por projeto em [policy.severities].",
                "Ten rules, with severity configurable per project in [policy.severities].",
              )}
            </p>
            <div className="overflow-hidden rounded-xl border border-[var(--border)] transition-transform duration-300 hover:-translate-y-1">
              {deterministicRules.map((item, index) => (
                <div
                  key={item.rule}
                  className={`flex flex-col gap-1 bg-[var(--bg-alt)] px-5 py-3 sm:flex-row sm:items-center sm:gap-4 ${
                    index < deterministicRules.length - 1
                      ? "border-b border-[var(--border)]"
                      : ""
                  }`}
                >
                  <code className="text-base text-[var(--text-h)] sm:w-64 sm:shrink-0">
                    {item.rule}
                  </code>
                  <span
                    className={`text-xs font-semibold uppercase sm:w-16 sm:shrink-0 ${item.tone}`}
                  >
                    {item.severity}
                  </span>
                  <span className="text-base text-[var(--text)]/70">
                    {item.when}
                  </span>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal>
            <h2
              id="skill-sentry-cases"
              className="mt-14 text-xl font-semibold text-[var(--text-h)]"
            >
              {t("Skill sentry-cases", "sentry-cases skill")}
            </h2>
            {lang === "pt" ? (
              <p className="text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Gerada pelo <Cmd>sentry init</Cmd> em{" "}
                <span className="text-[var(--text-h)]">
                  .claude/skills/sentry-cases/SKILL.md
                </span>
                , carregada automaticamente pelo Claude Code. Recebe o pedido em
                texto livre, cria a spec, pergunta antes de escrever toda
                ambiguidade que mude um caso, preenche o{" "}
                <span className="text-[var(--text-h)]">CASES.md</span>, liga
                cada caso ao teste com{" "}
                <span className="text-[var(--text-h)]"># cenario:</span> e roda{" "}
                <Cmd>check</Cmd> até fechar limpo. Nunca escreve status. Para
                outros agentes, o mesmo fluxo vive em{" "}
                <span className="text-[var(--text-h)]">AGENT-SENTRY.md</span> na
                raiz do projeto.
              </p>
            ) : (
              <p className="text-justify text-lg leading-relaxed text-[var(--text)]/80">
                Generated by <Cmd>sentry init</Cmd> at{" "}
                <span className="text-[var(--text-h)]">
                  .claude/skills/sentry-cases/SKILL.md
                </span>
                , loaded automatically by Claude Code. It receives the free-text
                request, creates the spec, asks before writing anything
                ambiguous that would change a case, fills in{" "}
                <span className="text-[var(--text-h)]">CASES.md</span>, links
                each case to a test with{" "}
                <span className="text-[var(--text-h)]"># scenario:</span>, and
                runs <Cmd>check</Cmd> until it's clean. It never writes status.
                For other agents, the same flow lives in{" "}
                <span className="text-[var(--text-h)]">AGENT-SENTRY.md</span> at
                the project root.
              </p>
            )}
          </Reveal>

          <PageFooter
            prevLabel={t("O fluxo de trabalho", "The workflow")}
            onPrevClick={onPrevClick}
            nextLabel="Papers"
            onNextClick={onNextClick}
            className="mt-14"
          />
        </div>

        <DocsSidebar
          sections={commandsSectionsByLang[lang]}
          label={t("Nesta página", "On this page")}
        />
      </div>
    </div>
  );
}

const PaperIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path
      d="M7 3h7l4 4v13a1 1 0 01-1 1H7a1 1 0 01-1-1V4a1 1 0 011-1z"
      strokeLinejoin="round"
    />
    <path d="M9 12h6M9 15h6M9 9h2" strokeLinecap="round" />
  </svg>
);

const QuoteIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    aria-hidden="true"
  >
    <path
      d="M7 8a3 3 0 00-3 3v2a3 3 0 003 3M7 8c0-2 1-4 3-5M17 8a3 3 0 00-3 3v2a3 3 0 003 3m0-8c0-2 1-4 3-5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const TransformIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    aria-hidden="true"
  >
    <path
      d="M4 7h11a4 4 0 014 4v1M20 17H9a4 4 0 01-4-4v-1"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M15 4l3 3-3 3M9 20l-3-3 3-3"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const GroundIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    aria-hidden="true"
  >
    <circle cx="12" cy="6" r="2" />
    <path
      d="M12 8v4M6 20v-4a2 2 0 012-2h8a2 2 0 012 2v4M6 20h12"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

type FlowStep = { icon: ReactNode; label: string };

type Paper = {
  id: string;
  eyebrow: string;
  title: string;
  authors: string;
  venue: string;
  summary: ReactNode;
  principle: string;
  flow: FlowStep[];
  grounds: ReactNode[];
  href?: string;
};

const FlowArrowIcon = () => (
  <svg
    aria-hidden="true"
    className="hidden shrink-0 text-[var(--accent)] sm:block"
    width="40"
    height="16"
    viewBox="0 0 40 16"
    fill="none"
  >
    <path
      d="M0 8h34M28 2l6 6-6 6"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

function FlowDiagram({ steps }: { steps: FlowStep[] }) {
  return (
    <div className="flex flex-wrap justify-center gap-x-2 gap-y-4">
      {steps.map((step, index) => (
        <div
          key={`${step.label}-${index}`}
          className="flex w-24 flex-col items-center text-center"
        >
          <div className="flex w-full items-center justify-center gap-2">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-alt)] text-[var(--accent)] [&>svg]:h-5 [&>svg]:w-5">
              {step.icon}
            </span>
            {index < steps.length - 1 && <FlowArrowIcon />}
          </div>
          <p className="mt-2 w-full break-words text-xs leading-snug text-[var(--text-h)]">
            {step.label}
          </p>
        </div>
      ))}
    </div>
  );
}

function SectionLabel({
  icon,
  children,
}: {
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--text)]/50">
      <span className="text-[var(--accent)]">{icon}</span>
      {children}
    </p>
  );
}

function PrincipleQuote({ children }: { children: ReactNode }) {
  return (
    <blockquote className="relative mt-3 border-l-2 border-[var(--accent)] pl-4 text-justify text-base italic leading-relaxed text-[var(--text)]/80">
      <span
        aria-hidden="true"
        className="mr-1 font-serif text-2xl not-italic leading-none text-[var(--accent)]"
      >
        “
      </span>
      {children}
    </blockquote>
  );
}

function GroundsList({ items }: { items: ReactNode[] }) {
  return (
    <ul className="mt-2 rounded-lg border border-[var(--border)] px-4 py-3 space-y-1.5">
      {items.map((item, index) => (
        <li
          key={index}
          className="flex items-start gap-2 text-base leading-relaxed text-[var(--text)]/70"
        >
          <span
            aria-hidden="true"
            className="mt-2 h-1 w-1 shrink-0 rounded-full bg-[var(--accent)]"
          />
          <span className="text-justify">{item}</span>
        </li>
      ))}
    </ul>
  );
}

const papersByLang: Record<"pt" | "en", Paper[]> = {
  pt: [
    {
      id: "test-impact-analysis",
      eyebrow: "Test Impact Analysis",
      title:
        "An approach for Test Impact Analysis on the Integration Level in Java programs",
      authors: "Muzammil Shahbaz — Thales Underwater Systems",
      venue: "arXiv:2211.07782",
      summary:
        "Seleciona testes de integração com base na análise de impacto das mudanças de código em runtime, reduzindo a suíte executada em CI/CD em até 50% em média e mais de 80% em alguns cenários.",
      principle: "Teste o que mudou, não o sistema inteiro.",
      flow: [
        { icon: <PaperIcon />, label: "Paper" },
        { icon: <ScanIcon />, label: "Test Impact Analysis" },
        { icon: <SlidersIcon />, label: "Cobertura da mudança" },
        { icon: <IssueIcon />, label: "changed-code-uncovered" },
        { icon: <ReportIcon />, label: "Veredito auditável" },
      ],
      grounds: [
        <>
          Análise do diff — delimita exatamente o que entrou em escopo na
          execução
        </>,
        <>
          <W>changed-code-uncovered</W> — dispara quando o diff altera código
          sem teste que o exercite
        </>,
        <>
          <W>coverage-below-threshold</W> — compara a cobertura da mudança com o
          mínimo do <W>policy.thresholds</W>
        </>,
        <>
          <W>changed_coverage</W> — limiar configurável em [policy.thresholds]
          no <W>sentry.toml</W>
        </>,
        <>
          Cobertura da mudança — mede o código alterado, não o repositório
          inteiro
        </>,
      ],
      href: "https://arxiv.org/pdf/2211.07782",
    },
    {
      id: "risk-based-testing",
      eyebrow: "Risk-Based Testing",
      title: "A Taxonomy of Risk-Based Testing",
      authors: "Michael Felderer, Ina Schieferdecker",
      venue: "STTT · arXiv:1912.11519",
      summary:
        "Taxonomia para categorizar abordagens de teste orientadas a risco, cobrindo motivadores, avaliação e processos de teste guiados por risco.",
      principle: "A severidade deve refletir o risco, não apenas a falha.",
      flow: [
        { icon: <PaperIcon />, label: "Paper" },
        { icon: <ScanIcon />, label: "Risk-Based Testing" },
        { icon: <IssueIcon />, label: "Avaliação do risco" },
        { icon: <SlidersIcon />, label: "policy.severities" },
        { icon: <ReportIcon />, label: "Priorização dos achados" },
      ],
      grounds: [
        <>
          <W>policy.severities</W> — sobrescreve a severidade de qualquer regra,
          achado a achado
        </>,
        <>
          Regras críticas e de alta severidade — bloqueiam o veredito antes das
          demais
        </>,
        <>
          Priorização dos achados — ordena o relatório pelo risco, não pela
          ordem de execução
        </>,
        <>
          Classes de equivalência — cobrem os cenários que concentram maior
          risco
        </>,
        <>
          Veredito baseado em evidências — cada severidade carrega a
          justificativa que a gerou
        </>,
      ],
      href: "https://arxiv.org/pdf/1912.11519",
    },
    {
      id: "shift-left",
      eyebrow: "Shift Left",
      title: "What is Shift-Left Testing?",
      authors: "Rahul Awati — TechTarget",
      venue: "TechTarget · 2023",
      summary:
        "Define shift-left testing como a prática de mover atividades de qualidade para estágios mais iniciais do ciclo de desenvolvimento, reduzindo custos e tempo de correção.",
      principle: "A intenção do teste deve existir antes da implementação.",
      flow: [
        { icon: <PenIcon />, label: "Pedido" },
        { icon: <TerminalIcon />, label: "CASES.md" },
        { icon: <FlowIcon />, label: "Implementação" },
        { icon: <RunIcon />, label: "Teste associado" },
        { icon: <ReportIcon />, label: "Veredito" },
      ],
      grounds: [
        <>
          <W>CASES.md</W> — declara a intenção antes de qualquer linha de código
          ser escrita
        </>,
        <>
          <W>PROMPT.md</W> — preserva o pedido original como fonte da verdade
        </>,
        <>
          <Cmd>sentry check</Cmd> — valida vocabulário e estrutura antes de
          rodar qualquer teste
        </>,
        <>
          Fluxo orientado à mudança — liga caso a teste antes do merge, não
          depois
        </>,
        <>
          Relatório versionado — o veredito aparece no diff da PR, antes da
          revisão humana
        </>,
      ],
      href: "https://www.techtarget.com/searchitoperations/definition/shift-left-testing",
    },
    {
      id: "test-pyramid",
      eyebrow: "Test Pyramid",
      title: "Test Pyramid Engineering Guidance",
      authors: "UK Home Office — Engineering Standards",
      venue: "Home Office Engineering Guidance and Standards",
      summary:
        "Guia prático para a aplicação da pirâmide de testes: maior volume de testes unitários, menos testes de integração e uma camada ainda menor de testes end-to-end.",
      principle:
        "Cada nível da pirâmide produz um tipo diferente de evidência.",
      flow: [
        { icon: <RunIcon />, label: "Testes unitários" },
        { icon: <FlowIcon />, label: "Testes de integração" },
        { icon: <SlidersIcon />, label: "Cobertura" },
        { icon: <ReportIcon />, label: "Evidências" },
        { icon: <HistoryIcon />, label: "Veredito" },
      ],
      grounds: [
        <>
          Cinco dimensões de cobertura — requisitos, integrações, erros,
          segurança e interface
        </>,
        <>
          Testes de integração — camada intermediária cobrando contratos e
          persistência
        </>,
        <>
          <W>changed-code-uncovered</W> — cobra teste unitário no código
          alterado, a base da pirâmide
        </>,
        <>
          Camada frontend via Playwright — evidência de execução e2e, nunca
          cobertura de linha
        </>,
        <>
          Evidências por camada — cada nível da pirâmide sustenta um tipo
          diferente de prova
        </>,
      ],
      href: "https://engineering.homeoffice.gov.uk/standards/test-pyramid/",
    },
    {
      id: "requirements-traceability",
      eyebrow: "Requirements Traceability",
      title: "An Analysis of the Requirements Traceability Problem",
      authors: "Orlena Gotel, Anthony Finkelstein",
      venue: "IEEE ICRE 1994",
      summary:
        "Define e categoriza o problema de rastreabilidade de requisitos, distinguindo rastreabilidade pré-especificação (por que o requisito existe) de pós-especificação (onde ele foi verificado) — a maioria dos problemas vem da primeira, não da segunda.",
      principle:
        "Todo requisito precisa apontar para onde foi verificado, não só para onde foi implementado.",
      flow: [
        { icon: <PenIcon />, label: "Requisito" },
        { icon: <TerminalIcon />, label: "CASES.md" },
        { icon: <ScanIcon />, label: "Marcador # cenario:" },
        { icon: <RunIcon />, label: "Teste real" },
        { icon: <ReportIcon />, label: "Rastreabilidade auditável" },
      ],
      grounds: [
        <>
          <W>requirement-without-scenario</W> — dispara quando um requisito do
          prompt não vira nenhum caso
        </>,
        <>
          <W>scenario-without-test</W> — dispara quando um caso do CASES.md não
          tem teste associado
        </>,
        <>
          <W>orphan-scenario-marker</W> — dispara quando o marcador aponta pra
          um caso que não existe
        </>,
        <>
          Marcador <W># cenario:</W> — liga o teste ao nome exato do caso, não a
          uma convenção de arquivo
        </>,
        <>
          Rastreabilidade multi-stack — o mesmo marcador funciona em qualquer
          linguagem com comentário
        </>,
      ],
      href: "http://csis.pace.edu/~ogotel/research/GOTEL93%20An%20Analysis%20of%20the%20Requirements%20Traceability%20Problem.pdf",
    },
    {
      id: "flaky-tests",
      eyebrow: "Flaky Tests",
      title: "An Empirical Analysis of Flaky Tests",
      authors: "Qingzhou Luo, Farah Hariri, Lamyaa Eloussi, Darko Marinov",
      venue: "ACM FSE 2014",
      summary:
        "Estudo empírico de 201 commits que corrigiram testes instáveis (flaky) em 51 projetos open source, catalogando as causas mais comuns de um teste passar ou falhar sem nenhuma mudança de código.",
      principle:
        "Um veredito só é confiável se o mesmo commit sempre produzir o mesmo resultado.",
      flow: [
        { icon: <BranchIcon />, label: "Commit" },
        { icon: <RunIcon />, label: "Execução da suíte" },
        { icon: <IssueIcon />, label: "Zero chamada de IA" },
        { icon: <ReportIcon />, label: "Veredito determinístico" },
        { icon: <HistoryIcon />, label: "Histórico comparável" },
      ],
      grounds: [
        <>
          Zero chamada de IA — nenhum modelo é invocado, então não há fonte de
          variação do lado do Sentry
        </>,
        <>
          <W>test-failing</W> — reprova por teste que falhou de verdade, nunca
          por variação entre rodadas
        </>,
        <>
          Suíte declarada em <W>[tests]</W>/<W>[e2e]</W> — o comando executado é
          sempre o mesmo, commit a commit
        </>,
        <>
          Cache por hash — reaproveita a última execução completa quando as
          entradas não mudaram, sem medir de novo
        </>,
        <>
          Histórico auditável — duas execuções do mesmo commit são comparáveis
          porque o resultado não varia
        </>,
      ],
      href: "https://mir.cs.illinois.edu/lamyaa/publications/fse14.pdf",
    },
    {
      id: "regression-test-selection",
      eyebrow: "Regression Test Selection",
      title: "Analyzing Regression Test Selection Techniques",
      authors: "Gregg Rothermel, Mary Jean Harrold",
      venue: "IEEE Transactions on Software Engineering, 1996",
      summary:
        "Compara técnicas de seleção de testes de regressão por segurança, precisão e custo: decidir quais testes re-executar depois de uma mudança, em vez de rodar a suíte inteira sempre.",
      principle: "Nem toda mudança justifica rodar a suíte inteira de novo.",
      flow: [
        { icon: <PenIcon />, label: "Arquivo salvo" },
        { icon: <ScanIcon />, label: "sentry watch" },
        { icon: <SlidersIcon />, label: "Modo instantâneo" },
        { icon: <RunIcon />, label: "Escalada pra suíte" },
        { icon: <ReportIcon />, label: "Veredito atualizado" },
      ],
      grounds: [
        <>
          <Cmd>sentry watch</Cmd> — reavalia ao salvar, e só escala pra suíte
          completa quando o arquivo salvo é um teste
        </>,
        <>
          Modo instantâneo — sem mudança na suíte declarada, não há por que
          medir de novo
        </>,
        <>
          Cache por hash — reusa a última execução completa quando as entradas
          não mudaram
        </>,
        <>
          Análise de impacto — decide o que está em escopo sem precisar re-rodar
          tudo
        </>,
        <>Modo completo — sempre chamado antes do veredito valer para o CI</>,
      ],
      href: "https://doi.org/10.1109/32.536955",
    },
  ],
  en: [
    {
      id: "test-impact-analysis",
      eyebrow: "Test Impact Analysis",
      title:
        "An approach for Test Impact Analysis on the Integration Level in Java programs",
      authors: "Muzammil Shahbaz — Thales Underwater Systems",
      venue: "arXiv:2211.07782",
      summary:
        "Selects integration tests based on runtime analysis of code-change impact, cutting the suite executed in CI/CD by up to 50% on average, over 80% in some scenarios.",
      principle: "Test what changed, not the entire system.",
      flow: [
        { icon: <PaperIcon />, label: "Paper" },
        { icon: <ScanIcon />, label: "Test Impact Analysis" },
        { icon: <SlidersIcon />, label: "Changed-code coverage" },
        { icon: <IssueIcon />, label: "changed-code-uncovered" },
        { icon: <ReportIcon />, label: "Auditable verdict" },
      ],
      grounds: [
        <>Diff analysis — pins down exactly what's in scope for the run</>,
        <>
          <W>changed-code-uncovered</W> — fires when the diff touches code with
          no test exercising it
        </>,
        <>
          <W>coverage-below-threshold</W> — compares changed-code coverage
          against <W>policy.thresholds</W>' minimum
        </>,
        <>
          <W>changed_coverage</W> — configurable threshold in
          [policy.thresholds] in <W>sentry.toml</W>
        </>,
        <>
          Changed-code coverage — measures the changed code, not the whole
          repository
        </>,
      ],
      href: "https://arxiv.org/pdf/2211.07782",
    },
    {
      id: "risk-based-testing",
      eyebrow: "Risk-Based Testing",
      title: "A Taxonomy of Risk-Based Testing",
      authors: "Michael Felderer, Ina Schieferdecker",
      venue: "STTT · arXiv:1912.11519",
      summary:
        "A taxonomy for categorizing risk-based testing approaches, covering risk drivers, risk assessment and the risk-based test process.",
      principle: "Severity should reflect risk, not just the failure.",
      flow: [
        { icon: <PaperIcon />, label: "Paper" },
        { icon: <ScanIcon />, label: "Risk-Based Testing" },
        { icon: <IssueIcon />, label: "Risk assessment" },
        { icon: <SlidersIcon />, label: "policy.severities" },
        { icon: <ReportIcon />, label: "Finding prioritization" },
      ],
      grounds: [
        <>
          <W>policy.severities</W> — overrides the severity of any rule, finding
          by finding
        </>,
        <>
          Critical and high-severity rules — block the verdict ahead of the rest
        </>,
        <>
          Finding prioritization — orders the report by risk, not by execution
          order
        </>,
        <>
          Equivalence classes — cover the scenarios that concentrate the most
          risk
        </>,
        <>
          Evidence-based verdict — every severity carries the justification
          behind it
        </>,
      ],
      href: "https://arxiv.org/pdf/1912.11519",
    },
    {
      id: "shift-left",
      eyebrow: "Shift Left",
      title: "What is Shift-Left Testing?",
      authors: "Rahul Awati — TechTarget",
      venue: "TechTarget · 2023",
      summary:
        "Defines shift-left testing as moving quality activities to earlier stages of the development cycle, cutting cost and fix time.",
      principle: "Test intent must exist before implementation.",
      flow: [
        { icon: <PenIcon />, label: "Request" },
        { icon: <TerminalIcon />, label: "CASES.md" },
        { icon: <FlowIcon />, label: "Implementation" },
        { icon: <RunIcon />, label: "Associated test" },
        { icon: <ReportIcon />, label: "Verdict" },
      ],
      grounds: [
        <>
          <W>CASES.md</W> — declares intent before a single line of code is
          written
        </>,
        <>
          <W>PROMPT.md</W> — preserves the original request as the source of
          truth
        </>,
        <>
          <Cmd>sentry check</Cmd> — validates vocabulary and structure before
          running any test
        </>,
        <>
          Change-oriented flow — links case to test before the merge, not after
        </>,
        <>
          Versioned report — the verdict shows up in the PR diff, ahead of human
          review
        </>,
      ],
      href: "https://www.techtarget.com/searchitoperations/definition/shift-left-testing",
    },
    {
      id: "test-pyramid",
      eyebrow: "Test Pyramid",
      title: "Test Pyramid Engineering Guidance",
      authors: "UK Home Office — Engineering Standards",
      venue: "Home Office Engineering Guidance and Standards",
      summary:
        "Practical guidance on applying the test pyramid: more unit tests, fewer integration tests, and an even thinner layer of end-to-end tests.",
      principle:
        "Each level of the pyramid produces a different kind of evidence.",
      flow: [
        { icon: <RunIcon />, label: "Unit tests" },
        { icon: <FlowIcon />, label: "Integration tests" },
        { icon: <SlidersIcon />, label: "Coverage" },
        { icon: <ReportIcon />, label: "Evidence" },
        { icon: <HistoryIcon />, label: "Verdict" },
      ],
      grounds: [
        <>
          Five coverage dimensions — requirements, integrations, errors,
          security and interface
        </>,
        <>
          Integration tests — the middle layer, covering contracts and
          persistence
        </>,
        <>
          <W>changed-code-uncovered</W> — requires a unit test on changed code,
          the base of the pyramid
        </>,
        <>
          Frontend layer via Playwright — e2e execution evidence, never line
          coverage
        </>,
        <>
          Evidence per layer — each level of the pyramid supports a different
          kind of proof
        </>,
      ],
      href: "https://engineering.homeoffice.gov.uk/standards/test-pyramid/",
    },
    {
      id: "requirements-traceability",
      eyebrow: "Requirements Traceability",
      title: "An Analysis of the Requirements Traceability Problem",
      authors: "Orlena Gotel, Anthony Finkelstein",
      venue: "IEEE ICRE 1994",
      summary:
        "Defines and categorizes the requirements traceability problem, distinguishing pre-requirements-specification traceability (why the requirement exists) from post-specification traceability (where it was verified) — most traceability problems come from the former, not the latter.",
      principle:
        "Every requirement must point to where it was verified, not just where it was implemented.",
      flow: [
        { icon: <PenIcon />, label: "Requirement" },
        { icon: <TerminalIcon />, label: "CASES.md" },
        { icon: <ScanIcon />, label: "# cenario: marker" },
        { icon: <RunIcon />, label: "Real test" },
        { icon: <ReportIcon />, label: "Auditable traceability" },
      ],
      grounds: [
        <>
          <W>requirement-without-scenario</W> — fires when a requirement from
          the prompt never becomes a case
        </>,
        <>
          <W>scenario-without-test</W> — fires when a case in CASES.md has no
          associated test
        </>,
        <>
          <W>orphan-scenario-marker</W> — fires when the marker points to a case
          that doesn't exist
        </>,
        <>
          The <W># cenario:</W> marker — links the test to the case's exact
          name, not a file naming convention
        </>,
        <>
          Multi-stack traceability — the same marker works in any language that
          supports comments
        </>,
      ],
      href: "http://csis.pace.edu/~ogotel/research/GOTEL93%20An%20Analysis%20of%20the%20Requirements%20Traceability%20Problem.pdf",
    },
    {
      id: "flaky-tests",
      eyebrow: "Flaky Tests",
      title: "An Empirical Analysis of Flaky Tests",
      authors: "Qingzhou Luo, Farah Hariri, Lamyaa Eloussi, Darko Marinov",
      venue: "ACM FSE 2014",
      summary:
        "Empirical study of 201 commits that fixed flaky tests across 51 open-source projects, cataloging the most common causes of a test passing or failing with no code change at all.",
      principle:
        "A verdict is only trustworthy if the same commit always produces the same result.",
      flow: [
        { icon: <BranchIcon />, label: "Commit" },
        { icon: <RunIcon />, label: "Suite run" },
        { icon: <IssueIcon />, label: "Zero AI calls" },
        { icon: <ReportIcon />, label: "Deterministic verdict" },
        { icon: <HistoryIcon />, label: "Comparable history" },
      ],
      grounds: [
        <>
          Zero AI calls — no model is ever invoked, so there's no source of
          variation on Sentry's side
        </>,
        <>
          <W>test-failing</W> — fails on a test that actually failed, never on
          variance between runs
        </>,
        <>
          Suite declared in <W>[tests]</W>/<W>[e2e]</W> — the command executed
          is always the same, commit to commit
        </>,
        <>
          Hash-based cache — reuses the last full run when the inputs haven't
          changed, instead of measuring again
        </>,
        <>
          Auditable history — two runs of the same commit are comparable because
          the result doesn't vary
        </>,
      ],
      href: "https://mir.cs.illinois.edu/lamyaa/publications/fse14.pdf",
    },
    {
      id: "regression-test-selection",
      eyebrow: "Regression Test Selection",
      title: "Analyzing Regression Test Selection Techniques",
      authors: "Gregg Rothermel, Mary Jean Harrold",
      venue: "IEEE Transactions on Software Engineering, 1996",
      summary:
        "Compares regression test selection techniques by safety, precision and cost: deciding which tests to re-run after a change instead of always running the whole suite.",
      principle: "Not every change justifies running the whole suite again.",
      flow: [
        { icon: <PenIcon />, label: "File saved" },
        { icon: <ScanIcon />, label: "sentry watch" },
        { icon: <SlidersIcon />, label: "Instant mode" },
        { icon: <RunIcon />, label: "Escalates to the suite" },
        { icon: <ReportIcon />, label: "Updated verdict" },
      ],
      grounds: [
        <>
          <Cmd>sentry watch</Cmd> — re-evaluates on save, and only escalates to
          the full suite when the saved file is a test
        </>,
        <>
          Instant mode — with no change to the declared suite, there's nothing
          new to measure
        </>,
        <>
          Hash-based cache — reuses the last full run when the inputs haven't
          changed
        </>,
        <>
          Impact analysis — decides what's in scope without having to re-run
          everything
        </>,
        <>
          Complete mode — always the one called before the verdict counts for CI
        </>,
      ],
      href: "https://doi.org/10.1109/32.536955",
    },
  ],
};

function PapersContent({ onPrevClick }: { onPrevClick: () => void }) {
  const { lang, t } = useLanguage();
  const papers = papersByLang[lang];
  const sections = useMemo(
    () => papers.map((paper) => ({ id: paper.id, label: paper.eyebrow })),
    [papers],
  );

  return (
    <div className="mx-auto max-w-5xl px-6 pb-14 pt-6">
      <div className="flex gap-8 lg:gap-12">
        <div className="min-w-0 flex-1">
          <Reveal>
            <h1 className="text-3xl font-semibold uppercase tracking-normal text-[var(--text-h)]">
              Papers
            </h1>
            <p className="mt-6 text-justify text-lg leading-relaxed text-[var(--text)]/80">
              {lang === "pt" ? (
                <>
                  As regras do{" "}
                  <span className="text-[var(--text-h)]">Sentry</span> não foram
                  definidas arbitrariamente. Cada mecanismo da ferramenta
                  (análise de impacto, cobertura da mudança, severidade, classes
                  de equivalência e veredito auditável) está apoiado em práticas
                  estabelecidas da engenharia de qualidade de software. Leituras
                  para quem quer entender o raciocínio por trás das regras, não
                  apenas como utilizá-las.
                </>
              ) : (
                <>
                  <span className="text-[var(--text-h)]">Sentry</span>'s rules
                  weren't defined arbitrarily. Every mechanism in the tool
                  (impact analysis, changed-code coverage, severity, equivalence
                  classes and the auditable verdict) is grounded in established
                  software quality engineering practice. Reading for anyone who
                  wants to understand the reasoning behind the rules, not just
                  how to use them.
                </>
              )}
            </p>
          </Reveal>

          {papers.map((paper) => {
            const cardContent = (
              <>
                <div className="flex items-start justify-between gap-3 text-[var(--accent)]">
                  <PaperIcon />
                  {paper.href && <ExternalIcon />}
                </div>
                <h3 className="mt-3 text-lg font-semibold text-[var(--accent)]">
                  {paper.title}
                </h3>
                <p className="mt-2 text-base text-white">
                  {paper.authors} ·{" "}
                  <span className="text-[var(--accent)]">{paper.venue}</span>
                </p>
                <div className="mb-4 mt-4 h-px w-6 bg-[var(--border)]" />
                <p className="text-justify text-base leading-relaxed text-[var(--text)]/70">
                  {paper.summary}
                </p>

                <div className="mt-4">
                  <SectionLabel icon={<QuoteIcon />}>
                    {t("Princípio", "Principle")}
                  </SectionLabel>
                </div>
                <PrincipleQuote>{paper.principle}</PrincipleQuote>

                <div className="mt-5">
                  <SectionLabel icon={<TransformIcon />}>
                    {t(
                      "Como isso se transforma no Sentry",
                      "How this becomes Sentry",
                    )}
                  </SectionLabel>
                </div>
                <div className="mt-5">
                  <FlowDiagram steps={paper.flow} />
                </div>

                <div className="mt-5">
                  <SectionLabel icon={<GroundIcon />}>
                    {t("Fundamenta", "Grounds")}
                  </SectionLabel>
                </div>
                <GroundsList items={paper.grounds} />
              </>
            );

            return (
              <Reveal key={paper.id} className="mt-8">
                {paper.href ? (
                  <a
                    id={paper.id}
                    href={paper.href}
                    target="_blank"
                    rel="noreferrer"
                    className="glow-card block scroll-mt-24 cursor-pointer rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] px-6 py-5 transition-colors duration-200 hover:border-[var(--accent)]/40"
                  >
                    {cardContent}
                  </a>
                ) : (
                  <div
                    id={paper.id}
                    className="glow-card scroll-mt-24 rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] px-6 py-5 transition-colors duration-200 hover:border-[var(--accent)]/40"
                  >
                    {cardContent}
                  </div>
                )}
              </Reveal>
            );
          })}

          <PageFooter
            prevLabel={t("Comandos e Habilidades", "Commands & Skills")}
            onPrevClick={onPrevClick}
            className="mt-14"
          />
        </div>

        <DocsSidebar
          sections={sections}
          label={t("Nesta página", "On this page")}
        />
      </div>
    </div>
  );
}

export function DocsPage() {
  const { lang, t } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabIds = useMemo(() => tabs.map((tab) => tab.id), []);
  const requestedTab = searchParams.get("tab");
  const activeTab =
    requestedTab && tabIds.includes(requestedTab) ? requestedTab : tabs[0].id;
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });
  const [hoverTab, setHoverTab] = useState<string | null>(null);
  const [tabsMenuOpen, setTabsMenuOpen] = useState(false);
  const tabsNavRef = useRef<HTMLElement | null>(null);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const indicatorTarget = hoverTab ?? activeTab;

  function goToTab(id: string) {
    setTabsMenuOpen(false);
    setSearchParams((params) => {
      const next = new URLSearchParams(params);
      next.set("tab", id);
      return next;
    });
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }

  useEffect(() => {
    const el = tabRefs.current[indicatorTarget];
    if (el) {
      setIndicator({ left: el.offsetLeft, width: el.offsetWidth });
    }
  }, [indicatorTarget, lang]);

  useEffect(() => {
    const container = tabsNavRef.current;
    const el = tabRefs.current[activeTab];
    if (container && el) {
      const target =
        el.offsetLeft - container.clientWidth / 2 + el.clientWidth / 2;
      container.scrollTo({ left: target, behavior: "smooth" });
    }
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <div className="border-b border-[var(--border)]">
        <nav
          ref={tabsNavRef}
          className="scroll-fade-x relative mx-auto hidden w-fit max-w-full items-center justify-center gap-6 overflow-x-auto px-6 text-sm md:flex"
          onMouseLeave={() => setHoverTab(null)}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              ref={(el) => {
                tabRefs.current[tab.id] = el;
              }}
              type="button"
              onClick={() => goToTab(tab.id)}
              onMouseEnter={() => setHoverTab(tab.id)}
              className={`cursor-pointer whitespace-nowrap py-3 transition-colors duration-300 ${
                activeTab === tab.id
                  ? "text-[var(--accent)]"
                  : "text-[var(--text)]/60 hover:text-[var(--accent)]"
              }`}
            >
              {tab[lang]}
            </button>
          ))}
          <span
            aria-hidden="true"
            className="pointer-events-none absolute bottom-0 h-[2px] rounded-full bg-[var(--accent)] transition-all duration-300 ease-out"
            style={{ left: indicator.left, width: indicator.width }}
          />
        </nav>

        <div className="md:hidden">
          <button
            type="button"
            aria-label={t("Abrir menu das seções", "Open sections menu")}
            aria-expanded={tabsMenuOpen}
            aria-controls="docs-tabs-menu"
            onClick={() => setTabsMenuOpen((value) => !value)}
            className="flex w-full cursor-pointer items-center justify-center gap-2 px-6 py-3 text-sm text-[var(--text-h)]"
          >
            <span>{tabs.find((tab) => tab.id === activeTab)?.[lang]}</span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              className={`shrink-0 text-[var(--accent)] transition-transform duration-200 ${tabsMenuOpen ? "rotate-180" : ""}`}
            >
              <path d="m6 9 6 6 6-6" />
            </svg>
          </button>
          <AnimatePresence initial={false}>
            {tabsMenuOpen && (
            <motion.div
              key="docs-tabs-menu"
              variants={menuPanel}
              initial="hidden"
              animate="show"
              exit="hidden"
              className="overflow-hidden"
            >
            <ul id="docs-tabs-menu" className="border-t border-[var(--border)] px-6 py-2 text-sm">
              {tabs.map((tab) => (
                <motion.li key={tab.id} variants={menuItem}>
                  <button
                    type="button"
                    onClick={() => goToTab(tab.id)}
                    className={`w-full cursor-pointer py-2.5 text-left transition-colors duration-200 ${
                      activeTab === tab.id
                        ? "text-[var(--accent)]"
                        : "text-[var(--text)]/60 hover:text-[var(--accent)]"
                    }`}
                  >
                    {tab[lang]}
                  </button>
                </motion.li>
              ))}
            </ul>
            </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {activeTab === "start" && (
        <>
          <section className="relative mx-auto max-w-5xl overflow-hidden px-6 pt-20 pb-4">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute -top-24 left-1/2 h-[360px] w-[720px] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(57,255,20,0.22),rgba(57,255,20,0.07),transparent)] blur-3xl"
            />

            <div className="group relative flex flex-col items-center text-center">
              <span
                aria-hidden="true"
                className="absolute -top-3 left-0 h-4 w-4 border-t-2 border-l-2 border-[var(--accent)]/60 transition-all duration-300 ease-out group-hover:-translate-x-1 group-hover:-translate-y-1 group-hover:border-[var(--accent)]"
              />
              <span
                aria-hidden="true"
                className="absolute -top-3 right-0 h-4 w-4 border-t-2 border-r-2 border-[var(--accent)]/60 transition-all duration-300 ease-out group-hover:translate-x-1 group-hover:-translate-y-1 group-hover:border-[var(--accent)]"
              />
              <span
                aria-hidden="true"
                className="absolute -bottom-3 left-0 h-4 w-4 border-b-2 border-l-2 border-[var(--accent)]/60 transition-all duration-300 ease-out group-hover:-translate-x-1 group-hover:translate-y-1 group-hover:border-[var(--accent)]"
              />
              <span
                aria-hidden="true"
                className="absolute -bottom-3 right-0 h-4 w-4 border-b-2 border-r-2 border-[var(--accent)]/60 transition-all duration-300 ease-out group-hover:translate-x-1 group-hover:translate-y-1 group-hover:border-[var(--accent)]"
              />

              <h1
                className="max-w-2xl text-4xl font-semibold uppercase leading-tight tracking-normal sm:text-5xl"
                key={`${lang}-docs-h1`}
              >
                <span className="sr-only">
                  {t(
                    "Bem-vindo à documentação do Sentry",
                    "Welcome to the Sentry docs",
                  )}
                </span>
                <span
                  aria-hidden="true"
                  className="pointer-events-none select-none"
                >
                  <BlurReveal as="span" className="block">
                    {t("Bem-vindo à documentação", "Welcome to the")}
                  </BlurReveal>
                  <BlurReveal as="span" className="block" delay={0.15}>
                    {t("do Sentry", "Sentry docs")}
                  </BlurReveal>
                </span>
              </h1>
              <p className="mt-4 w-full text-base leading-relaxed text-[var(--text-muted)]">
                {t(
                  "Instale a CLI, escreva a spec com seu agente de IA e rode o ciclo intenção → veredito direto do terminal.",
                  "Install the CLI, write the spec with your AI agent, and run the intent → verdict cycle straight from the terminal.",
                )}
              </p>

              <div className="mt-10 w-full max-w-lg text-left">
                <TerminalWindow lines={heroLines[lang]} title="sentry" />
              </div>
            </div>
          </section>
          <GetStartedContent onNextClick={() => goToTab("setup")} />
        </>
      )}

      {activeTab === "setup" && (
        <SetupContent
          onPrevClick={() => goToTab("start")}
          onNextClick={() => goToTab("workflow")}
        />
      )}

      {activeTab === "workflow" && (
        <WorkflowContent
          onPrevClick={() => goToTab("setup")}
          onNextClick={() => goToTab("commands")}
        />
      )}

      {activeTab === "commands" && (
        <CommandsContent
          onPrevClick={() => goToTab("workflow")}
          onNextClick={() => goToTab("papers")}
        />
      )}

      {activeTab === "papers" && (
        <PapersContent onPrevClick={() => goToTab("commands")} />
      )}
    </div>
  );
}

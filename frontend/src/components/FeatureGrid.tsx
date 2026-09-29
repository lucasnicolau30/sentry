import { FeatureCard } from "./FeatureCard";
import { Reveal } from "./Reveal";
import { useLanguage } from "../i18n/LanguageContext";
import arrowIcon from "../assets/arrow-icon.png";

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

const TargetIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="5" />
    <circle cx="12" cy="12" r="1" />
  </svg>
);

const ShieldIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" />
    <path d="M9 12l2 2 4-4" />
  </svg>
);

const HistoryIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 3" />
  </svg>
);

const LayersIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <path d="M12 3l8 4-8 4-8-4 8-4z" />
    <path d="M4 11l8 4 8-4" />
    <path d="M4 15l8 4 8-4" />
  </svg>
);

const CpuIcon = () => (
  <svg {...iconProps} aria-hidden="true">
    <rect x="7" y="7" width="10" height="10" rx="1.5" />
    <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l1.8 1.8M17.2 17.2 19 19M19 5l-1.8 1.8M6.8 17.2 5 19" />
  </svg>
);

const featuresByLang = {
  pt: [
    {
      icon: <TargetIcon />,
      title: "Cobertura do que mudou",
      description: (
        <>
          95% de cobertura no projeto inteiro não impede a linha que você acabou de mudar de ficar sem teste nenhum.
          O <span className="text-[var(--text-h)]">Sentry</span> mede exatamente o{" "}
          diff, não a média que esconde isso.
        </>
      ),
    },
    {
      icon: <ShieldIcon />,
      title: "Veredito com contexto",
      description: (
        <>
          Um CI verde não significa que alguém leu o resultado. O veredito (aprovado, reprovado ou inconclusivo)
          sai como código de saída, pronto para travar o merge sozinho.
        </>
      ),
    },
    {
      icon: <HistoryIcon />,
      title: "Histórico auditável",
      description: (
        <>
          Queda de cobertura costuma só aparecer quando já é tarde. Cada execução fica salva e comparável com a
          anterior, e a regressão aparece no dia em que aconteceu, não três sprints depois.
        </>
      ),
    },
    {
      icon: <LayersIcon />,
      title: (
        <span className="inline-flex items-center gap-1.5">
          Rastreabilidade caso
          <img src={arrowIcon} alt="" aria-hidden="true" className="h-3 w-auto" />
          teste
        </span>
      ),
      description: (
        <>
          Um teste vazio passa em qualquer suíte e não prova nada. Cada caso do{" "}
          <span className="text-[var(--text-h)]">CASES.md</span> se liga a um teste real por um marcador de
          comentário; sem ele, o <span className="text-[var(--text-h)]">Sentry</span> não inventa que foi coberto.
        </>
      ),
    },
    {
      icon: <CpuIcon />,
      title: "Zero chamada de IA",
      description: (
        <>
          Rodar a mesma mudança duas vezes num revisor de IA pode dar dois vereditos diferentes, e cada rodada tem
          custo de token. O <span className="text-[var(--text-h)]">Sentry</span> não chama nenhum modelo: é{" "}
          determinístico, e o mesmo commit sempre produz o mesmo
          resultado, de graça.
        </>
      ),
      wide: true,
    },
  ],
  en: [
    {
      icon: <TargetIcon />,
      title: "Coverage of what changed",
      description: (
        <>
          95% coverage on the whole project doesn't stop the line you just changed from having zero tests.{" "}
          <span className="text-[var(--text-h)]">Sentry</span> measures the{" "}
          diff itself, not the average that hides it.
        </>
      ),
    },
    {
      icon: <ShieldIcon />,
      title: "Verdict with context",
      description: (
        <>
          A green CI doesn't mean anyone read the result. The verdict (passed, failed or inconclusive) comes out as
          an exit code, ready to block the merge on its own.
        </>
      ),
    },
    {
      icon: <HistoryIcon />,
      title: "Auditable history",
      description: (
        <>
          Coverage regressions usually surface once it's already too late. Every run is saved and compared against
          the last one, and a drop shows up the day it happened, not three sprints later.
        </>
      ),
    },
    {
      icon: <LayersIcon />,
      title: (
        <span className="inline-flex items-center gap-1.5">
          Case
          <img src={arrowIcon} alt="" aria-hidden="true" className="h-3 w-auto" />
          test traceability
        </span>
      ),
      description: (
        <>
          An empty test passes in any suite and proves nothing. Every case in{" "}
          <span className="text-[var(--text-h)]">CASES.md</span> links to a real test through a comment marker;
          without it, <span className="text-[var(--text-h)]">Sentry</span> never assumes it was covered.
        </>
      ),
    },
    {
      icon: <CpuIcon />,
      title: "Zero AI calls",
      description: (
        <>
          Running the same change twice through an AI reviewer can give two different verdicts, and every run costs
          tokens. <span className="text-[var(--text-h)]">Sentry</span> calls no model at all: it's{" "}
          deterministic, and the same commit always produces the same
          result, for free.
        </>
      ),
      wide: true,
    },
  ],
};

export function FeatureGrid() {
  const { lang } = useLanguage();
  const features = featuresByLang[lang];

  return (
    <section className="mx-auto max-w-5xl px-6 py-10">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {features.map(({ wide, ...feature }, index) => (
          <Reveal key={index} delay={index * 0.08} className={wide ? "h-full sm:col-span-2" : "h-full"}>
            <FeatureCard {...feature} />
          </Reveal>
        ))}
      </div>

    </section>
  );
}

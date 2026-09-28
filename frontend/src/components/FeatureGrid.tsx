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

const featuresByLang = {
  pt: [
    {
      icon: <TargetIcon />,
      title: "Cobertura do que mudou",
      description:
        "Prioriza a cobertura do código alterado em cada mudança, em vez de esconder lacunas na média geral do projeto.",
    },
    {
      icon: <ShieldIcon />,
      title: "Veredito com contexto",
      description:
        "Aprovado, reprovado ou inconclusivo com base em severidade e evidência real, nunca por ausência de dados.",
    },
    {
      icon: <HistoryIcon />,
      title: "Histórico auditável",
      description:
        "Cada execução é persistida e comparável: cobertura, testes e achados evoluindo lado a lado ao longo do tempo.",
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
          Cada caso do <span className="text-[var(--text-h)]">CASES.md</span> se liga ao teste real por um marcador de
          comentário, sem isso o <span className="text-[var(--text-h)]">Sentry</span> não inventa que foi coberto.
        </>
      ),
    },
  ],
  en: [
    {
      icon: <TargetIcon />,
      title: "Coverage of what changed",
      description:
        "Prioritizes coverage of the changed code on every change, instead of hiding gaps in the project's overall average.",
    },
    {
      icon: <ShieldIcon />,
      title: "Verdict with context",
      description: "Passed, failed or inconclusive based on severity and real evidence, never on missing data.",
    },
    {
      icon: <HistoryIcon />,
      title: "Auditable history",
      description: "Every run is persisted and comparable: coverage, tests and findings evolving side by side over time.",
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
          Every case in <span className="text-[var(--text-h)]">CASES.md</span> links to a real test through a comment marker —
          without it, <span className="text-[var(--text-h)]">Sentry</span> never assumes it was covered.
        </>
      ),
    },
  ],
};

export function FeatureGrid() {
  const { lang } = useLanguage();
  const features = featuresByLang[lang];

  return (
    <section className="mx-auto max-w-5xl px-6 py-10">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {features.map((feature, index) => (
          <Reveal key={index} delay={index * 0.08} className="h-full">
            <FeatureCard {...feature} />
          </Reveal>
        ))}
      </div>

    </section>
  );
}

import { FeatureCard } from "./FeatureCard";

const iconProps = {
  width: 20,
  height: 20,
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

const features = [
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
    title: "Consistência de frontend",
    description:
      "Verifica se componentes do mesmo papel reutilizam a base compartilhada, não só se o backend está coberto.",
  },
];

export function FeatureGrid() {
  return (
    <section className="mx-auto max-w-5xl px-6 py-10">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {features.map((feature) => (
          <FeatureCard key={feature.title} {...feature} />
        ))}
      </div>
    </section>
  );
}

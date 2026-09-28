import type { ReactNode } from "react";

type FeatureCardProps = {
  icon: ReactNode;
  title: ReactNode;
  description: ReactNode;
};

export function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="glow-card flex h-full flex-col rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] px-7 py-6 transition-colors duration-200 hover:border-[var(--accent)]/40">
      <div className="mb-3 text-[var(--accent)]">{icon}</div>
      <h3 className="mb-3 text-lg font-semibold">{title}</h3>
      <div className="mb-4 h-px w-6 bg-[var(--border)]" />
      <p className="text-justify text-base leading-relaxed text-[var(--text)]/70">{description}</p>
    </div>
  );
}

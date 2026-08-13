import type { ReactNode } from "react";

type FeatureCardProps = {
  icon: ReactNode;
  title: ReactNode;
  description: ReactNode;
};

export function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="glow-card rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] px-6 py-5 transition-colors duration-200 hover:border-[var(--accent)]/40">
      <div className="mb-3 text-[var(--accent)]">{icon}</div>
      <h3 className="mb-3 text-base font-semibold">{title}</h3>
      <div className="mb-4 h-px w-6 bg-[var(--border)]" />
      <p className="text-sm leading-relaxed text-[var(--text)]/70">{description}</p>
    </div>
  );
}

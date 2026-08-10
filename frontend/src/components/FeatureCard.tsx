import type { ReactNode } from "react";

type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  description: string;
};

export function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] p-6">
      <div className="mb-3 text-[var(--text-h)]">{icon}</div>
      <h3 className="mb-2 text-base font-semibold">{title}</h3>
      <p className="text-sm leading-relaxed text-[var(--text)]">{description}</p>
    </div>
  );
}

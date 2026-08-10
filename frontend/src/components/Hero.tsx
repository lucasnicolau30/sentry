import { InstallCommand } from "./InstallCommand";

export function Hero() {
  return (
    <section className="relative mx-auto max-w-5xl px-6 pt-20 pb-4">
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
          A disciplina entre
          <br />o commit e a confiança
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-[var(--accent)] sm:text-lg">
          O agente de IA declara a intenção; o Sentry mede a realidade: roda a suíte, lê o diff e a
          cobertura, e emite um veredito auditável.
        </p>

        <div className="mt-8">
          <InstallCommand />
        </div>
      </div>
    </section>
  );
}

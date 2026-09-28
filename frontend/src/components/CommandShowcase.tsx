import { TerminalWindow } from "./TerminalWindow";
import { Reveal } from "./Reveal";
import { useLanguage } from "../i18n/LanguageContext";

const commandsByLang = {
  pt: [
    {
      title: "Estrutura da spec",
      description: (
        <>
          Valida <span className="text-[var(--text-h)]">CASES.md</span>: vocabulário, estrutura e classes de equivalência
          cobradas.
        </>
      ),
      lines: [
        { text: "sentry check cadastro-de-cliente", tone: "command" as const },
        { text: "3 caso(s), 1 campo(s)", tone: "info" as const },
        { text: "✓ Estrutura válida e catálogo de classes coberto.", tone: "success" as const },
      ],
    },
    {
      title: "Comparação de execuções",
      description: "Compara as duas últimas execuções: cobertura, testes e achados novos ou resolvidos.",
      lines: [
        { text: "sentry history", tone: "command" as const },
        { text: "Comparando execução 1d88027b -> 83b0123a", tone: "info" as const },
        { text: "Cobertura global: +5.88%", tone: "info" as const },
        { text: "✓ Veredito: aprovado -> aprovado.", tone: "success" as const },
      ],
    },
    {
      title: "Execução com cobertura",
      description: "Roda a suíte, lê diff e cobertura, aplica as regras e persiste o veredito.",
      lines: [
        { text: "sentry run --spec cadastro-de-cliente --run-tests", tone: "command" as const },
        { text: "Cobertura do código alterado: 100%", tone: "info" as const },
        { text: "✓ Veredito: aprovado.", tone: "success" as const },
      ],
    },
  ],
  en: [
    {
      title: "Spec structure",
      description: (
        <>
          Validates <span className="text-[var(--text-h)]">CASES.md</span>: vocabulary, structure and required equivalence
          classes.
        </>
      ),
      lines: [
        { text: "sentry check cadastro-de-cliente", tone: "command" as const },
        { text: "3 case(s), 1 field(s)", tone: "info" as const },
        { text: "✓ Valid structure, class catalog covered.", tone: "success" as const },
      ],
    },
    {
      title: "Run comparison",
      description: "Compares the last two runs: coverage, tests and new or resolved findings.",
      lines: [
        { text: "sentry history", tone: "command" as const },
        { text: "Comparing run 1d88027b -> 83b0123a", tone: "info" as const },
        { text: "Global coverage: +5.88%", tone: "info" as const },
        { text: "✓ Verdict: passed -> passed.", tone: "success" as const },
      ],
    },
    {
      title: "Run with coverage",
      description: "Runs the suite, reads diff and coverage, applies the rules and persists the verdict.",
      lines: [
        { text: "sentry run --spec cadastro-de-cliente --run-tests", tone: "command" as const },
        { text: "Changed code coverage: 100%", tone: "info" as const },
        { text: "✓ Verdict: passed.", tone: "success" as const },
      ],
    },
  ],
};

export function CommandShowcase() {
  const { lang, t } = useLanguage();
  const commands = commandsByLang[lang];

  return (
    <section className="mx-auto max-w-5xl px-6 py-14">
      <Reveal>
        <h2 className="text-center text-3xl font-semibold uppercase tracking-normal sm:text-4xl">
          {t("Na prática", "In practice")}
        </h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-base text-[var(--text)]/60 sm:text-lg">
          {t("Cada comando com o output que ele realmente produz.", "Every command with the output it actually produces.")}
        </p>
      </Reveal>

      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {commands.map((item, index) => (
          <Reveal key={item.title} delay={index * 0.12}>
            <div className="flex flex-col gap-3 transition-transform duration-300 hover:-translate-y-1">
              <TerminalWindow lines={item.lines} title="sentry" />
              <div>
                <h3 className="text-base font-semibold">{item.title}</h3>
                <p className="mt-1 text-justify text-base leading-relaxed text-[var(--text)]/60">{item.description}</p>
              </div>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

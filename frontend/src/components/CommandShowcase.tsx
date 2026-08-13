import { TerminalWindow } from "./TerminalWindow";
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
        { text: "Validando estrutura...", tone: "info" as const },
        { text: "Classes de equivalência: 6/6 cobertas", tone: "info" as const },
        { text: "✓ Spec válida.", tone: "success" as const },
      ],
    },
    {
      title: "Execução com cobertura",
      description: "Roda a suíte, lê diff e cobertura, aplica as regras e persiste o veredito.",
      lines: [
        { text: "sentry run --spec cadastro-de-cliente --run-tests", tone: "command" as const },
        { text: "Executando suíte...", tone: "info" as const },
        { text: "Cobertura do código alterado: 92%", tone: "info" as const },
        { text: "✓ Veredito: aprovado.", tone: "success" as const },
      ],
    },
    {
      title: "Comparação de execuções",
      description: "Compara as duas últimas execuções: cobertura, testes e achados novos ou resolvidos.",
      lines: [
        { text: "sentry history", tone: "command" as const },
        { text: "Comparando execução #12 -> #13...", tone: "info" as const },
        { text: "2 achados resolvidos, 0 novos", tone: "info" as const },
        { text: "✓ Cobertura +4.2%.", tone: "success" as const },
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
        { text: "sentry check customer-registration", tone: "command" as const },
        { text: "Validating structure...", tone: "info" as const },
        { text: "Equivalence classes: 6/6 covered", tone: "info" as const },
        { text: "✓ Valid spec.", tone: "success" as const },
      ],
    },
    {
      title: "Run with coverage",
      description: "Runs the suite, reads diff and coverage, applies the rules and persists the verdict.",
      lines: [
        { text: "sentry run --spec customer-registration --run-tests", tone: "command" as const },
        { text: "Running suite...", tone: "info" as const },
        { text: "Changed code coverage: 92%", tone: "info" as const },
        { text: "✓ Verdict: passed.", tone: "success" as const },
      ],
    },
    {
      title: "Run comparison",
      description: "Compares the last two runs: coverage, tests and new or resolved findings.",
      lines: [
        { text: "sentry history", tone: "command" as const },
        { text: "Comparing run #12 -> #13...", tone: "info" as const },
        { text: "2 findings resolved, 0 new", tone: "info" as const },
        { text: "✓ Coverage +4.2%.", tone: "success" as const },
      ],
    },
  ],
};

export function CommandShowcase() {
  const { lang, t } = useLanguage();
  const commands = commandsByLang[lang];

  return (
    <section className="mx-auto max-w-5xl px-6 py-14">
      <h2 className="text-center text-2xl font-semibold uppercase tracking-normal sm:text-3xl">
        {t("Na prática", "In practice")}
      </h2>
      <p className="mx-auto mt-2 max-w-xl text-center text-sm text-[var(--text)]/60 sm:text-base">
        {t("Cada comando com o output que ele realmente produz.", "Every command with the output it actually produces.")}
      </p>

      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {commands.map((item) => (
          <div key={item.title} className="flex flex-col gap-3">
            <TerminalWindow lines={item.lines} title="sentry" />
            <div>
              <h3 className="text-sm font-semibold">{item.title}</h3>
              <p className="mt-1 text-sm leading-relaxed text-[var(--text)]/60">{item.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

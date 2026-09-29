import { InstallCommand } from "./InstallCommand";
import { BlurReveal } from "./blur-reveal";
import { Particles } from "./Particles";
import { useLanguage } from "../i18n/LanguageContext";

export function Hero() {
  const { lang, t } = useLanguage();

  return (
    <section className="relative overflow-hidden pt-16 pb-20">
      <div className="relative z-10 mx-auto flex max-w-5xl flex-col items-center px-6 text-center">
        {/* Bloco 1: título + subtítulo — isolado, sem nada por trás */}
        <div className="flex w-full flex-col items-center">
          <h1
            className="w-full max-w-4xl font-sans text-[clamp(32px,4.2vw,64px)] font-semibold leading-[1.05] tracking-[-0.03em] text-[var(--text-h)]"
            key={`${lang}-h1`}
          >
            <span className="sr-only">
              {t(
                "Seu agente escreveu o código. O Sentry garante que ele testou.",
                "Your agent wrote the code. Sentry makes sure it's tested.",
              )}
            </span>
            <span
              aria-hidden="true"
              className="pointer-events-none select-none"
            >
              <BlurReveal as="span" className="block" inView once={false}>
                {t("Seu agente escreveu o código.", "Your agent wrote the code.")}
              </BlurReveal>
              <span className="block">
                <BlurReveal
                  as="span"
                  className="inline"
                  delay={0.15}
                  inView
                  once={false}
                >
                  {t("O Sentry garante que ele", "Sentry makes sure it's")}
                </BlurReveal>{" "}
                <BlurReveal
                  as="span"
                  className="inline text-[var(--accent)]"
                  delay={0.25}
                  inView
                  once={false}
                >
                  {t("testou.", "tested.")}
                </BlurReveal>
              </span>
            </span>
          </h1>
          <p className="mt-8 max-w-3xl text-balance lg:whitespace-nowrap text-[clamp(13px,2.4vw,19px)] leading-[1.6] text-[var(--text-muted)]">
            {t(
              "Valide seus casos de teste e veja se o código alterado está coberto antes de aprovar a mudança.",
              "Validate your test cases and check whether the changed code is covered before approving the change.",
            )}
          </p>
        </div>

        {/* Bloco 2: gradiente + comando de instalação — separado do bloco do título */}
        <div
          className="relative -mt-6 flex h-[380px] w-screen mx-[calc(50%-50vw)] items-center justify-center overflow-hidden"
        >
          <img
            src="/images/hero-beam.png"
            alt=""
            aria-hidden="true"
            className="pointer-events-none absolute left-1/2 top-1/2 z-0 w-full max-w-none -translate-x-1/2 -translate-y-1/2 select-none opacity-45"
            style={{
              maskImage:
                "radial-gradient(55% 60% at 50% 50%, black 35%, transparent 85%)",
              WebkitMaskImage:
                "radial-gradient(55% 60% at 50% 50%, black 35%, transparent 85%)",
            }}
          />
          <Particles count={30} />
          <div className="relative z-10 -translate-y-4">
            <InstallCommand />
          </div>
        </div>
      </div>
    </section>
  );
}

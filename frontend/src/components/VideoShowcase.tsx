import { Reveal } from "./Reveal";
import { useLanguage } from "../i18n/LanguageContext";

export function VideoShowcase() {
  const { lang, t } = useLanguage();

  return (
    <section id="video" aria-labelledby="video-title" className="mx-auto max-w-5xl px-6 py-14">
      <Reveal>
        <h2 id="video-title" className="text-center text-3xl font-semibold uppercase tracking-normal sm:text-4xl">
          {t("Veja o Sentry em ação", "See Sentry in action")}
        </h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-base text-[var(--text)]/60 sm:text-lg">
          {t(
            "Do código do agente ao veredito auditável, e dos testes ao vídeo.",
            "From the agent's code to an auditable verdict, and from tests to video."
          )}
        </p>
      </Reveal>

      <Reveal delay={0.1} className="mt-10">
        <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--bg-alt)] shadow-[0_0_40px_-12px_rgba(57,255,20,0.25)]">
          <video
            key={lang}
            className="aspect-video w-full"
            controls
            playsInline
            preload="metadata"
            poster={`/video/poster-${lang}.jpg`}
            aria-label={t("Vídeo de apresentação do Sentry", "Sentry presentation video")}
          >
            <source src={`/video/sentry-${lang}.mp4`} type="video/mp4" />
            {t("Seu navegador não reproduz este vídeo.", "Your browser can't play this video.")}
          </video>
        </div>
      </Reveal>
    </section>
  );
}

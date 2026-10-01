import { useRef, useState } from "react";
import { Reveal } from "./Reveal";
import { useLanguage } from "../i18n/LanguageContext";

function PlayIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className="h-6 w-6 sm:h-8 sm:w-8">
      <path d="M8 5.5v13a1 1 0 001.5.86l11-6.5a1 1 0 000-1.72l-11-6.5A1 1 0 008 5.5z" />
    </svg>
  );
}

export function VideoShowcase() {
  const { lang, t } = useLanguage();
  const videoRef = useRef<HTMLVideoElement>(null);
  // O botão grande some quando o vídeo começa e volta quando ele termina ou
  // quando o idioma troca (o <video> é remontado com o outro arquivo).
  const [playingLang, setPlayingLang] = useState<string | null>(null);
  const started = playingLang === lang;

  const chips = [
    t("1:06 min", "1:06 min"),
    t("PT e EN", "PT and EN"),
  ];

  return (
    <section id="video" aria-labelledby="video-title" className="relative isolate mx-auto max-w-5xl px-6 py-16">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-1/3 -z-10 mx-auto h-72 max-w-3xl rounded-full bg-[var(--accent)]/10 blur-3xl"
      />

      <Reveal>
        <h2 id="video-title" className="text-center text-3xl font-semibold uppercase tracking-normal sm:text-4xl">
          {t("Vídeo promocional", "Promo video")}
        </h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-base text-[var(--text)]/60 sm:text-lg">
          {t(
            "O Sentry em pouco mais de um minuto: o agente escreve, o Sentry confere.",
            "Sentry in just over a minute: your agent writes, Sentry checks."
          )}
        </p>
      </Reveal>

      <Reveal delay={0.1} className="mt-10">
        <div className="overflow-hidden rounded-2xl border border-[var(--accent)]/30 bg-[var(--bg-alt)] shadow-[0_0_60px_-18px_rgba(57,255,20,0.45)]">
          <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f56]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#27c93f]" />
            <span className="ml-2 font-mono text-xs text-[var(--text)]/60">promo-{lang}.mp4</span>
            <span className="ml-auto hidden items-center gap-1.5 font-mono text-xs text-[var(--accent)] sm:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
              {t("gerado pelo Sentry", "made by Sentry")}
            </span>
          </div>

          <div className="relative bg-black">
            <video
              key={lang}
              ref={videoRef}
              className="aspect-video w-full"
              controls
              playsInline
              preload="metadata"
              poster={`/video/poster-${lang}.jpg`}
              aria-label={t("Vídeo promocional do Sentry", "Sentry promo video")}
              onPlay={() => setPlayingLang(lang)}
              onEnded={() => setPlayingLang(null)}
            >
              <source src={`/video/sentry-${lang}.mp4`} type="video/mp4" />
              {t("Seu navegador não reproduz este vídeo.", "Your browser can't play this video.")}
            </video>

            {!started && (
              <button
                type="button"
                onClick={() => videoRef.current?.play()}
                aria-label={t("Assistir ao vídeo promocional", "Watch the promo video")}
                className="group absolute inset-x-0 top-0 bottom-14 grid cursor-pointer place-items-center bg-black/55 transition-colors hover:bg-black/40"
              >
                <span className="flex flex-col items-center gap-3">
                  <span className="relative grid h-14 w-14 place-items-center sm:h-24 sm:w-24">
                    <span className="absolute inset-0 rounded-full bg-[var(--accent)]/40 motion-safe:animate-ping" />
                    <span className="relative grid h-full w-full place-items-center rounded-full bg-[var(--accent)] pl-1 text-black shadow-[0_0_40px_rgba(57,255,20,0.6)] transition-transform duration-200 group-hover:scale-105">
                      <PlayIcon />
                    </span>
                  </span>
                  <span className="hidden font-mono text-sm text-[var(--text-h)] sm:block">{t("Assistir · 1:06", "Watch · 1:06")}</span>
                </span>
              </button>
            )}
          </div>
        </div>
      </Reveal>

      <Reveal delay={0.2}>
        <ul className="mt-6 flex flex-wrap items-center justify-center gap-3 font-mono text-sm">
          {chips.map((chip) => (
            <li key={chip} className="rounded-full border border-[var(--border)] bg-[var(--bg-alt)] px-4 py-1.5 text-[var(--text)]/80">
              {chip}
            </li>
          ))}
          <li className="rounded-full border border-[var(--accent)]/30 bg-[var(--bg-alt)] px-4 py-1.5 text-[var(--text-h)]">
            <span className="text-[var(--accent)]">$ </span>sentry promo
          </li>
        </ul>
        <p className="mx-auto mt-4 max-w-xl text-center text-sm text-[var(--text)]/50">
          {t(
            "Quer mudar o vídeo? Peça ao agente: não precisa rodar o comando de novo.",
            "Want changes? Ask the agent: no need to run the command again."
          )}
        </p>
      </Reveal>
    </section>
  );
}

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { Reveal } from "./Reveal";
import { useLanguage } from "../i18n/LanguageContext";

// Tempo sem mexer o mouse até os controles sumirem, com o vídeo tocando.
const ESCONDER_APOS_MS = 1200;

const iconeBotao =
  "grid h-9 w-9 place-items-center rounded-full text-white transition-colors duration-200 hover:bg-white/10 hover:text-[var(--accent)] focus-visible:bg-white/10 focus-visible:text-[var(--accent)]";
const sombraIcone = "drop-shadow-[0_1px_3px_rgba(0,0,0,0.7)]";

function formatar(segundos: number) {
  if (!Number.isFinite(segundos)) return "0:00";
  const total = Math.floor(segundos);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

function preenchido(valor: number, maximo: number): CSSProperties {
  const pct = maximo > 0 ? Math.min(100, Math.max(0, (valor / maximo) * 100)) : 0;
  return { "--sr-track": `linear-gradient(to right, var(--accent) ${pct}%, rgba(255,255,255,0.25) ${pct}%)` } as CSSProperties;
}

function IconeVolume({ mudo }: { mudo: boolean }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className={`h-5 w-5 ${sombraIcone}`}>
      {mudo ? (
        <path d="M16.5 12A4.5 4.5 0 0014 7.97v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.8 8.8 0 0021 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06a8.99 8.99 0 003.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
      ) : (
        <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0014 7.97v8.05A4.5 4.5 0 0016.5 12zM14 3.23v2.06a7 7 0 010 13.42v2.06a9 9 0 000-17.54z" />
      )}
    </svg>
  );
}

function IconeTelaCheia({ ativa }: { ativa: boolean }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className={`h-5 w-5 ${sombraIcone}`}>
      {ativa ? (
        <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z" />
      ) : (
        <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" />
      )}
    </svg>
  );
}

export function VideoShowcase() {
  const { lang, t } = useLanguage();
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timerRef = useRef<number | undefined>(undefined);
  // O <video> é remontado quando o idioma troca, então o estado guarda em qual
  // idioma ele está tocando.
  const [playingLang, setPlayingLang] = useState<string | null>(null);
  const [visivel, setVisivel] = useState(true);
  const [tempo, setTempo] = useState(0);
  const [duracao, setDuracao] = useState(0);
  const [volume, setVolume] = useState(1);
  const [mudo, setMudo] = useState(false);
  const [telaCheia, setTelaCheia] = useState(false);
  const playing = playingLang === lang;
  // Parado ou pausado, o botão e os controles ficam sempre à mostra; tocando,
  // só enquanto o mouse se mexe.
  const mostrar = !playing || visivel;

  function mostrarPorUmTempo() {
    setVisivel(true);
    window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => setVisivel(false), ESCONDER_APOS_MS);
  }

  useEffect(() => () => window.clearTimeout(timerRef.current), []);

  useEffect(() => {
    const aoMudar = () => setTelaCheia(document.fullscreenElement === containerRef.current);
    document.addEventListener("fullscreenchange", aoMudar);
    return () => document.removeEventListener("fullscreenchange", aoMudar);
  }, []);

  function alternar() {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) void video.play();
    else video.pause();
  }

  function alternarSom() {
    const video = videoRef.current;
    if (!video) return;
    const novo = !video.muted;
    video.muted = novo;
    setMudo(novo);
    if (!novo && video.volume === 0) {
      video.volume = 0.5;
      setVolume(0.5);
    }
  }

  function mudarVolume(valor: number) {
    const video = videoRef.current;
    if (!video) return;
    video.volume = valor;
    video.muted = valor === 0;
    setVolume(valor);
    setMudo(valor === 0);
  }

  function alternarTelaCheia() {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void containerRef.current?.requestFullscreen();
  }

  const nivelVolume = mudo ? 0 : volume;

  return (
    <section id="video" aria-labelledby="video-title" className="mx-auto max-w-5xl px-6 py-14">
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
        <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] shadow-[0_0_24px_-8px_rgba(0,0,0,0.6)] transition-transform duration-300 hover:-translate-y-1">
          <div
            ref={containerRef}
            className={`relative bg-black ${telaCheia ? "flex h-screen w-screen items-center justify-center" : ""}`}
            onPointerMove={() => playing && mostrarPorUmTempo()}
          >
            <video
              key={lang}
              ref={videoRef}
              className={`aspect-video w-full ${telaCheia ? "max-h-full" : ""}`}
              playsInline
              preload="metadata"
              poster={`/video/poster-${lang}.jpg`}
              aria-label={t("Vídeo promocional do Sentry", "Sentry promo video")}
              onLoadedMetadata={(e) => {
                setDuracao(e.currentTarget.duration);
                setTempo(0);
                e.currentTarget.volume = volume;
                e.currentTarget.muted = mudo;
              }}
              onTimeUpdate={(e) => setTempo(e.currentTarget.currentTime)}
              onPlay={() => {
                setPlayingLang(lang);
                mostrarPorUmTempo();
              }}
              onPause={() => setPlayingLang(null)}
              onEnded={() => setPlayingLang(null)}
            >
              <source src={`/video/sentry-${lang}.mp4`} type="video/mp4" />
              {t("Seu navegador não reproduz este vídeo.", "Your browser can't play this video.")}
            </video>

            {/* Deixa a barra de controles livre embaixo. */}
            <button
              type="button"
              onClick={alternar}
              aria-label={
                playing ? t("Pausar o vídeo", "Pause the video") : t("Assistir ao vídeo promocional", "Watch the promo video")
              }
              className={`absolute inset-x-0 top-0 bottom-16 cursor-pointer transition-colors duration-200 focus-visible:[&>span]:opacity-100 ${
                playing ? "bg-transparent" : "bg-black/30 hover:bg-black/20"
              }`}
            >
              <span
                className={`absolute left-1/2 top-1/2 h-14 w-14 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--accent)] text-white shadow-[0_0_24px_rgba(57,255,20,0.45)] transition-[opacity,transform] duration-200 sm:h-20 sm:w-20 ${
                  mostrar ? "scale-100 opacity-100" : "scale-90 opacity-0"
                }`}
              >
                {/* Os dois ícones ficam no mesmo círculo e trocam com fade, cada um
                    centralizado pelo próprio contêiner. */}
                <span
                  aria-hidden="true"
                  className={`absolute inset-0 grid place-items-center transition-[opacity,transform] duration-200 ${
                    playing ? "scale-50 opacity-0" : "scale-100 opacity-100"
                  }`}
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6 sm:h-8 sm:w-8">
                    {/* Triângulo com a caixa um pouco à direita do centro: o peso visual
                        do triângulo fica à esquerda, e assim ele parece centralizado. */}
                    <path d="M8.2 5.4a.9.9 0 011.35-.78l9.6 6.6a.9.9 0 010 1.56l-9.6 6.6A.9.9 0 018.2 18.6V5.4z" />
                  </svg>
                </span>
                <span
                  aria-hidden="true"
                  className={`absolute inset-0 grid place-items-center transition-[opacity,transform] duration-200 ${
                    playing ? "scale-100 opacity-100" : "scale-50 opacity-0"
                  }`}
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6 sm:h-8 sm:w-8">
                    <rect x="6.5" y="5" width="4" height="14" rx="1.2" />
                    <rect x="13.5" y="5" width="4" height="14" rx="1.2" />
                  </svg>
                </span>
              </span>
            </button>

            {/* Barra de controles: progresso, tempo, volume vertical e tela cheia. */}
            <div
              role="group"
              aria-label={t("Controles do vídeo", "Video controls")}
              className={`absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent px-3 pb-2 pt-8 transition-opacity duration-200 ${
                mostrar ? "opacity-100" : "pointer-events-none opacity-0"
              }`}
            >
              <input
                type="range"
                min={0}
                max={duracao || 0}
                step={0.1}
                value={tempo}
                onChange={(e) => {
                  const video = videoRef.current;
                  if (video) video.currentTime = Number(e.target.value);
                  setTempo(Number(e.target.value));
                }}
                aria-label={t("Progresso do vídeo", "Video progress")}
                style={preenchido(tempo, duracao)}
                className="sentry-range w-full"
              />
              <div className="mt-1 flex items-center justify-between">
                <span className="font-mono text-xs text-white [text-shadow:0_1px_3px_rgba(0,0,0,0.8)]">
                  {formatar(tempo)} / {formatar(duracao)}
                </span>
                <div className="flex items-center gap-1">
                  <div className="group/vol relative">
                    <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 pb-2 opacity-0 transition-opacity duration-150 group-focus-within/vol:pointer-events-auto group-focus-within/vol:opacity-100 group-hover/vol:pointer-events-auto group-hover/vol:opacity-100">
                      <div
                        data-volume-vertical
                        className="relative h-28 w-9 rounded-full bg-black/70 shadow-[0_0_16px_rgba(0,0,0,0.6)] backdrop-blur-sm"
                      >
                        <input
                          type="range"
                          min={0}
                          max={1}
                          step={0.02}
                          value={nivelVolume}
                          onChange={(e) => mudarVolume(Number(e.target.value))}
                          aria-label={t("Volume", "Volume")}
                          style={preenchido(nivelVolume, 1)}
                          className="sentry-range absolute left-1/2 top-1/2 w-20 -translate-x-1/2 -translate-y-1/2 -rotate-90"
                        />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={alternarSom}
                      aria-label={mudo ? t("Ativar o som", "Unmute") : t("Silenciar", "Mute")}
                      className={iconeBotao}
                    >
                      <IconeVolume mudo={mudo || volume === 0} />
                    </button>
                  </div>
                  <button
                    type="button"
                    onClick={alternarTelaCheia}
                    aria-label={telaCheia ? t("Sair da tela cheia", "Exit fullscreen") : t("Tela cheia", "Fullscreen")}
                    className={iconeBotao}
                  >
                    <IconeTelaCheia ativa={telaCheia} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

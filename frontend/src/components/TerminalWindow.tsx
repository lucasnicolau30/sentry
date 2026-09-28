import type { ReactNode } from "react";

type TerminalTone =
  | "command"
  | "info"
  | "success"
  | "muted"
  | "banner-bright"
  | "banner-mid"
  | "banner-dim";

type TerminalLine = {
  text?: string;
  tone?: TerminalTone;
  segments?: { text: string; tone?: TerminalTone }[];
};

type TerminalWindowProps = {
  title?: string;
  lines?: TerminalLine[];
  children?: ReactNode;
  className?: string;
};

const toneClass: Record<TerminalTone, string> = {
  command: "text-[var(--text-h)]",
  info: "text-[var(--text)]/70",
  success: "text-[var(--accent)]",
  muted: "text-[var(--text)]/60",
  "banner-bright": "text-[var(--wordmark-bright)]",
  "banner-mid": "text-[var(--wordmark-mid)]",
  "banner-dim": "text-[var(--wordmark-dim)]",
};

// A arte do wordmark só fecha certo com entrelinha curta: o desenho foi
// montado para linhas de terminal, uma linha por linha de texto.
const bannerTones: TerminalTone[] = ["banner-bright", "banner-mid", "banner-dim"];

export function TerminalWindow({ title = "sentry", lines, children, className = "" }: TerminalWindowProps) {
  return (
    <div
      className={`w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] shadow-[0_0_24px_-8px_rgba(0,0,0,0.6)] transition-transform duration-300 hover:-translate-y-1 ${className}`}
    >
      <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f56]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#27c93f]" />
        <span className="ml-2 font-mono text-xs text-[var(--text)]/60">{title}</span>
      </div>
      <div className="scroll-fade-x overflow-x-auto px-4 py-3.5 font-mono text-sm leading-relaxed">
        {lines
          ? lines.map((line, index) => {
              const tone = line.tone ?? "info";
              return (
                <p
                  key={index}
                  className={`whitespace-pre ${bannerTones.includes(tone) ? "leading-[1.05]" : ""} ${
                    toneClass[tone]
                  }`}
                >
                  {tone === "command" ? <span className="text-[var(--accent)]">$ </span> : null}
                  {line.segments
                    ? line.segments.map((segment, segmentIndex) => (
                        <span key={segmentIndex} className={toneClass[segment.tone ?? tone]}>
                          {segment.text}
                        </span>
                      ))
                    : // A linha em branco do terminal precisa de um caractere real:
                      // um <p> vazio colapsa a zero e o espaçamento some.
                      (line.text || "\u00A0")}
                </p>
              );
            })
          : children}
      </div>
    </div>
  );
}

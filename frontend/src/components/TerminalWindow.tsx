import type { ReactNode } from "react";

type TerminalLine = {
  text: string;
  tone?: "command" | "info" | "success" | "muted";
};

type TerminalWindowProps = {
  title?: string;
  lines?: TerminalLine[];
  children?: ReactNode;
  className?: string;
};

const toneClass: Record<NonNullable<TerminalLine["tone"]>, string> = {
  command: "text-[var(--text-h)]",
  info: "text-[var(--text)]/70",
  success: "text-[var(--accent)]",
  muted: "text-[var(--text)]/60",
};

export function TerminalWindow({ title = "sentry", lines, children, className = "" }: TerminalWindowProps) {
  return (
    <div
      className={`w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] shadow-[0_0_24px_-8px_rgba(0,0,0,0.6)] ${className}`}
    >
      <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f56]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#27c93f]" />
        <span className="ml-2 font-mono text-xs text-[var(--text)]/60">{title}</span>
      </div>
      <div
        className={`space-y-1 px-4 py-3.5 font-mono text-[13px] leading-relaxed ${
          lines ? "" : "scroll-fade-x overflow-x-auto"
        }`}
      >
        {lines
          ? lines.map((line, index) => (
              <p key={index} className={`whitespace-pre-wrap break-words ${toneClass[line.tone ?? "info"]}`}>
                {line.tone === "command" ? <span className="text-[var(--accent)]">$ </span> : null}
                {line.text}
              </p>
            ))
          : children}
      </div>
    </div>
  );
}

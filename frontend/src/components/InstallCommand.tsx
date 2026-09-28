import { useEffect, useState } from "react";

const COMMAND = "pip install sentry-test";

function useTypewriter(
  text: string,
  {
    typeSpeed = 55,
    deleteSpeed = 30,
    pauseAfterType = 1600,
    pauseAfterDelete = 400,
  } = {}
) {
  const [length, setLength] = useState(0);
  const [phase, setPhase] = useState<"typing" | "pausing" | "deleting">("typing");

  useEffect(() => {
    if (phase === "typing") {
      if (length < text.length) {
        const id = setTimeout(() => setLength((l) => l + 1), typeSpeed);
        return () => clearTimeout(id);
      }
      const id = setTimeout(() => setPhase("pausing"), pauseAfterType);
      return () => clearTimeout(id);
    }

    if (phase === "pausing") {
      const id = setTimeout(() => setPhase("deleting"), pauseAfterDelete);
      return () => clearTimeout(id);
    }

    // deleting
    if (length > 0) {
      const id = setTimeout(() => setLength((l) => l - 1), deleteSpeed);
      return () => clearTimeout(id);
    }
    const id = setTimeout(() => setPhase("typing"), pauseAfterDelete);
    return () => clearTimeout(id);
  }, [phase, length, text, typeSpeed, deleteSpeed, pauseAfterType, pauseAfterDelete]);

  return { output: text.slice(0, length), idle: phase === "pausing" };
}

const CopyIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="2" />
    <path
      d="M6 15H4.8A1.8 1.8 0 0 1 3 13.2V4.8A1.8 1.8 0 0 1 4.8 3h8.4A1.8 1.8 0 0 1 15 4.8V6"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M4 12l5 5L20 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export function InstallCommand() {
  const [copied, setCopied] = useState(false);
  const { output, idle } = useTypewriter(COMMAND);

  async function handleCopy() {
    await navigator.clipboard.writeText(COMMAND);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex w-fit max-w-full items-center gap-4 rounded-2xl border border-[var(--border)] bg-[var(--bg-alt)] px-5 py-3.5 shadow-[0_0_16px_-6px_rgba(255,255,255,0.08)]">
      <code className="flex items-baseline whitespace-nowrap font-mono text-base text-[var(--accent)] sm:text-lg">
        <span aria-hidden="true" className="flex items-baseline">
          <span>$ {output}</span>
          <span
            className={`ml-0.5 inline-block h-[1em] w-[2px] shrink-0 self-center bg-[var(--accent)] ${
              idle ? "animate-caret-blink" : "opacity-100"
            }`}
          />
        </span>
        <span className="sr-only">$ {COMMAND}</span>
      </code>
      <button
        type="button"
        onClick={handleCopy}
        aria-label="Copiar comando"
        className="flex shrink-0 cursor-pointer items-center justify-center text-[var(--accent)] transition-colors hover:text-[var(--text-h)]"
      >
        {copied ? <CheckIcon /> : <CopyIcon />}
      </button>
    </div>
  );
}

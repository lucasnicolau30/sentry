import { useState } from "react";

const COMMAND = "pip install sentry-test";

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

  async function handleCopy() {
    await navigator.clipboard.writeText(COMMAND);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex w-fit max-w-full items-center gap-4 rounded-2xl border border-[var(--border)] bg-[var(--bg-alt)] px-5 py-3.5 shadow-[0_0_16px_-6px_rgba(255,255,255,0.08)]">
      <code className="whitespace-nowrap font-mono text-sm text-[var(--text-h)] sm:text-base">
        <span className="text-[var(--accent)]">$</span> {COMMAND}
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

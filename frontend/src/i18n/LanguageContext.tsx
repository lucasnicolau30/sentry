import { createContext, useContext, useState, type ReactNode } from "react";

type Lang = "pt" | "en";

type LanguageContextValue = {
  lang: Lang;
  toggle: () => void;
  t: (pt: string, en: string) => string;
};

const STORAGE_KEY = "sentry-lang";

const LanguageContext = createContext<LanguageContextValue>({
  lang: "pt",
  toggle: () => {},
  t: (pt) => pt,
});

function readStoredLang(): Lang {
  if (typeof window === "undefined") return "pt";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === "en" ? "en" : "pt";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(readStoredLang);
  const toggle = () =>
    setLang((value) => {
      const next = value === "pt" ? "en" : "pt";
      window.localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  const t = (pt: string, en: string) => (lang === "pt" ? pt : en);

  return <LanguageContext.Provider value={{ lang, toggle, t }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  return useContext(LanguageContext);
}

import { createContext, useContext, useState, type ReactNode } from "react";

type Lang = "pt" | "en";

type LanguageContextValue = {
  lang: Lang;
  toggle: () => void;
  t: (pt: string, en: string) => string;
};

const LanguageContext = createContext<LanguageContextValue>({
  lang: "pt",
  toggle: () => {},
  t: (pt) => pt,
});

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("pt");
  const toggle = () => setLang((value) => (value === "pt" ? "en" : "pt"));
  const t = (pt: string, en: string) => (lang === "pt" ? pt : en);

  return <LanguageContext.Provider value={{ lang, toggle, t }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  return useContext(LanguageContext);
}

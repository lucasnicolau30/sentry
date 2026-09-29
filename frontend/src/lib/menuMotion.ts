import type { Variants } from "motion/react";

// Mesma sensação do Reveal do scroll: fade + subida de 18px, curva expo-out
// longa (0.35s). O painel abre em altura e cada item entra em cascata; ao
// fechar, tudo recolhe rápido para não segurar o clique seguinte.
const EASE = [0.16, 1, 0.3, 1] as const;

export const menuPanel: Variants = {
  hidden: {
    height: 0,
    opacity: 0,
    transition: { duration: 0.2, ease: EASE, when: "afterChildren" },
  },
  show: {
    height: "auto",
    opacity: 1,
    transition: { duration: 0.35, ease: EASE, when: "beforeChildren", staggerChildren: 0.04 },
  },
};

export const menuItem: Variants = {
  hidden: { opacity: 0, y: 18, transition: { duration: 0.15 } },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: EASE } },
};

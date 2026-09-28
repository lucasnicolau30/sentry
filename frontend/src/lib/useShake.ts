import { useAnimationControls } from "motion/react";

export function useShake() {
  const controls = useAnimationControls();

  const shake = () => {
    controls.start({
      scale: [1, 0.85, 1.08, 0.97, 1],
      transition: { duration: 0.4, ease: "easeInOut" },
    });
  };

  return { controls, shake };
}

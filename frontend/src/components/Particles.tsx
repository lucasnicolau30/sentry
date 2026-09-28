import { useMemo } from "react";
import { motion } from "motion/react";

type Particle = {
  left: number;
  top: number;
  size: number;
  driftX: number;
  driftY: number;
  duration: number;
  delay: number;
};

function makeParticles(count: number): Particle[] {
  return Array.from({ length: count }, () => ({
    left: Math.random() * 100,
    top: 15 + Math.random() * 70,
    size: 1 + Math.random() * 2.2,
    driftX: (Math.random() - 0.5) * 24,
    driftY: (Math.random() - 0.5) * 24,
    duration: 6 + Math.random() * 6,
    delay: Math.random() * -8,
  }));
}

export function Particles({ count = 28, className = "" }: { count?: number; className?: string }) {
  const particles = useMemo(() => makeParticles(count), [count]);

  return (
    <div aria-hidden="true" className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}>
      {particles.map((p, i) => (
        <motion.span
          key={i}
          className="absolute rounded-full bg-[var(--accent-hover,var(--accent))]"
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
            width: p.size,
            height: p.size,
            opacity: 0.35,
            boxShadow: `0 0 ${p.size * 4}px var(--accent)`,
          }}
          animate={{
            x: [0, p.driftX, 0],
            y: [0, p.driftY, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}

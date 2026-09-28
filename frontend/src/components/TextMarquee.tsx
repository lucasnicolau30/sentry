import { Children, cloneElement, isValidElement, type ReactElement, type ReactNode } from "react";

type TextMarqueeProps = {
  height: number;
  speed?: number;
  prefix?: ReactNode;
  children: ReactNode;
  className?: string;
};

// Marquee vertical: os itens sobem em loop contínuo dentro de uma janela de
// altura fixa. O conteúdo é duplicado uma vez -- ao alcançar -50% do total,
// a segunda cópia já está exatamente onde a primeira começou, então o corte
// da animação (volta de -50% pra 0%) fica invisível.
export function TextMarquee({ height, speed = 1, prefix, children, className = "" }: TextMarqueeProps) {
  const items = Children.toArray(children).filter(isValidElement) as ReactElement<{ children?: ReactNode }>[];
  const duplicated = [
    ...items,
    ...items.map((item, index) => cloneElement(item, { key: `dup-${index}` })),
  ];
  const duration = Math.max(6, items.length * 2.6) / speed;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {prefix}
      <div
        aria-hidden="true"
        className="relative overflow-hidden"
        style={{
          height,
          maskImage: "linear-gradient(to bottom, transparent, black 20%, black 80%, transparent)",
          WebkitMaskImage: "linear-gradient(to bottom, transparent, black 20%, black 80%, transparent)",
        }}
      >
        <div
          className="animate-text-marquee flex flex-col motion-reduce:animate-none"
          style={{ animationDuration: `${duration}s` }}
        >
          {duplicated}
        </div>
      </div>
      <span className="sr-only">
        {items.map((item) => (typeof item.props.children === "string" ? item.props.children : "")).join(", ")}
      </span>
    </div>
  );
}

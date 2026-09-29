import { useEffect } from "react";
import { motion } from "motion/react";
import { useLanguage } from "../i18n/LanguageContext";
import pug from "../assets/error-pug.webp";
import golden from "../assets/error-golden.webp";

// Contorno branco em volta do cachorro (efeito adesivo): sem ele, as partes pretas
// do pug se fundem com o número preto atrás. A sombra suave vem por último.
const STICKER_OUTLINE = [
  "drop-shadow(3px 0 0 #fff)",
  "drop-shadow(-3px 0 0 #fff)",
  "drop-shadow(0 3px 0 #fff)",
  "drop-shadow(0 -3px 0 #fff)",
  "drop-shadow(0 18px 24px rgba(0,0,0,0.25))",
].join(" ");

type ErrorPageProps = {
  code: string;
  title: string;
  message: string;
  image: string;
  imageClassName: string;
};

function ErrorPage({ code, title, message, image, imageClassName }: ErrorPageProps) {
  const { t } = useLanguage();

  useEffect(() => {
    const previous = document.title;
    document.title = `${code} · ${title}`;
    return () => {
      document.title = previous;
    };
  }, [code, title]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-white text-black">
      <div className="flex min-h-full flex-col items-center justify-center px-6 py-10">
        {/* Número e cachorro dividem a mesma célula: o número fica atrás, o cachorro na frente */}
        <div aria-hidden="true" className="grid select-none place-items-center">
          <p className="col-start-1 row-start-1 font-sans text-[clamp(170px,44vw,540px)] font-extrabold leading-[0.8] tracking-[-0.05em] text-black">
            {code}
          </p>
          <motion.img
            src={image}
            alt=""
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            style={{ filter: STICKER_OUTLINE }}
            className={`pointer-events-none col-start-1 row-start-1 -mb-5 self-end object-contain sm:-mb-9 ${imageClassName}`}
          />
        </div>

        <div className="mt-14 flex max-w-md flex-col items-center text-center">
          <h1 className="font-sans text-[clamp(22px,3.2vw,30px)] font-semibold leading-tight tracking-[-0.02em] text-black">{title}</h1>
          <p className="mt-3 text-balance text-base leading-relaxed text-black/60">{message}</p>
          <a
            href="/"
            className="group relative mt-6 inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-4"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              className="transition-transform duration-300 group-hover:-translate-x-1"
            >
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            {t("Voltar para a home", "Back to home")}
            <span
              aria-hidden="true"
              className="absolute -bottom-1 left-0 h-px w-full origin-left scale-x-0 bg-black transition-transform duration-300 ease-out group-hover:scale-x-100"
            />
          </a>
        </div>
      </div>
    </div>
  );
}

export function NotFoundPage() {
  const { t } = useLanguage();

  return (
    <ErrorPage
      code="404"
      title={t("Desculpa, não achamos essa página", "Sorry, we couldn't find that page")}
      message={t(
        "O endereço pode ter mudado ou nunca ter existido. O filhote já procurou por toda parte.",
        "The address may have changed or never existed. The pup has already looked everywhere.",
      )}
      image={pug}
      imageClassName="w-[min(78vw,640px)]"
    />
  );
}

export function ServerErrorPage() {
  const { t } = useLanguage();

  return (
    <ErrorPage
      code="500"
      title={t("Desculpa, algo deu errado do nosso lado", "Sorry, something went wrong on our side")}
      message={t(
        "Aconteceu um erro inesperado. Tente de novo em instantes.",
        "An unexpected error happened. Please try again in a moment.",
      )}
      image={golden}
      imageClassName="h-[min(48vh,520px)] w-auto max-w-[75vw] sm:h-[min(64vh,660px)]"
    />
  );
}

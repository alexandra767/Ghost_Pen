"use client";

import Image from "next/image";

interface PageHeroProps {
  title: string;
  subtitle?: string;
  image?: string;
}

export function PageHero({ title, subtitle, image }: PageHeroProps) {
  return (
    <section className="relative w-full overflow-hidden">
      {image ? (
        <>
          <div className="relative h-[40vh] min-h-[320px] w-full">
            <Image
              src={image}
              alt={title}
              fill
              className="object-cover"
              priority
            />
            <div className="absolute inset-0 bg-foreground/60" />
          </div>
          <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
            <h1
              className="text-4xl font-bold text-background sm:text-5xl"
              style={{ fontFamily: "var(--font-playfair)" }}
            >
              {title}
            </h1>
            {subtitle && (
              <p className="mt-4 max-w-xl text-lg text-background/70">
                {subtitle}
              </p>
            )}
          </div>
        </>
      ) : (
        <div className="bg-secondary border-b border-border">
          <div className="relative z-10 flex flex-col items-center justify-center px-4 py-20 text-center">
            <h1
              className="text-4xl font-bold text-foreground sm:text-5xl"
              style={{ fontFamily: "var(--font-playfair)" }}
            >
              {title}
            </h1>
            {subtitle && (
              <p className="mt-4 max-w-xl text-lg text-muted">
                {subtitle}
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

"use client";

interface PageHeroProps {
  title: string;
  subtitle?: string;
}

export function PageHero({ title, subtitle }: PageHeroProps) {
  return (
    <section className="relative w-full overflow-hidden bg-surface border-b border-border">
      <div className="relative z-10 flex flex-col items-center justify-center px-4 py-16 text-center">
        <h1
          className="text-4xl font-bold text-foreground sm:text-5xl"
          style={{ fontFamily: "var(--font-space)" }}
        >
          {title}
        </h1>
        {subtitle && (
          <p className="mt-4 max-w-xl text-lg text-muted">
            {subtitle}
          </p>
        )}
      </div>
    </section>
  );
}

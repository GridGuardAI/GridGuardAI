"use client";

export default function Header() {
  return (
    <header className="mb-12 flex items-end justify-between flex-wrap gap-6">
      <div>
        <h1
          className="text-[44px] md:text-[64px] font-bold leading-none tracking-tight text-glow-accent"
          style={{ color: "var(--accent)" }}
        >
          GridGuard AI
        </h1>
        <p className="mt-3 text-[15px] text-[var(--muted)] max-w-lg">
          Find what&apos;s wrong with your power system before it costs you more.
        </p>
      </div>

     
    </header>
  );
}

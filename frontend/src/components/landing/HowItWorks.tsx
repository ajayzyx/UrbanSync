const STEPS: [string, string, string][] = [
  ["01", "Connect", "Bring together urban datasets."],
  ["02", "Normalize", "Align coordinate systems and schemas."],
  ["03", "Match", "Identify corresponding spatial features."],
  ["04", "Validate", "Detect topology and data conflicts."],
  ["05", "Explain", "Score confidence and show evidence."],
  ["06", "Harmonize", "Create a unified review-ready spatial view."],
];

export function HowItWorks() {
  return (
    <section className="border-y border-line bg-panel-2/60" id="how">
      <div className="mx-auto max-w-6xl px-4 py-20 md:px-6">
        <div className="micro mb-2 text-accent">How it works</div>
        <h2 className="font-display text-[30px] font-medium tracking-tight md:text-[38px]">
          One workflow, from raw sources to a reviewed map
        </h2>
        <ol className="mt-10 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-6">
          {STEPS.map(([n, title, body]) => (
            <li key={n} className="bg-panel p-5">
              <div className="micro text-accent">{n}</div>
              <div className="font-display mt-2 text-[17px] font-medium">{title}</div>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

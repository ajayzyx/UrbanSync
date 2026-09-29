const SOURCES = ["Cadastral", "Revenue", "Municipal", "GNSS", "Drone", "Buildings", "Utilities"];
const DIFFER = ["Different systems", "Different schemas", "Different geometries", "Different identifiers"];
const ENGINE = ["Different sources", "Spatial + attribute intelligence", "Matched features", "Detected conflicts",
  "Explainable confidence", "Harmonized urban view"];

function Arrow() {
  return <div aria-hidden="true" className="py-1 text-center text-[15px] text-faint">↓</div>;
}

export function Solving() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-12 sm:py-14 md:px-6 lg:py-20" id="problem">
      <div className="micro mb-2 text-accent">The problem</div>
      <h2 className="font-display max-w-2xl text-[30px] leading-tight font-medium tracking-tight md:text-[38px]">
        What are we actually solving?
      </h2>
      <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-muted">
        Urban land information comes from many sources — cadastral maps, revenue records, municipal GIS, drone imagery,
        ORI, DSM/DTM, GNSS/CORS surveys, ground truthing, building footprints and utility networks. They can describe the
        same physical land with different coordinates, boundaries, identifiers, schemas, attributes and survey dates.
      </p>
      <div className="mt-7 grid grid-cols-1 gap-3 sm:mt-8 sm:grid-cols-2 sm:gap-4 lg:mt-10 lg:grid-cols-3">
        <div className="rounded-xl border border-line bg-panel p-5 lg:p-6">
          <div className="micro mb-4">Problem</div>
          <div className="flex flex-wrap gap-1.5">
            {SOURCES.map((s) => (
              <span key={s} className="rounded-md border border-line bg-panel-2 px-2 py-1 text-[12px]">{s}</span>
            ))}
          </div>
          <Arrow />
          <ul className="space-y-1 text-[13px] text-muted">{DIFFER.map((d) => <li key={d}>{d}</li>)}</ul>
          <Arrow />
          <p className="text-[14px] font-medium text-[#991b1b]">Manual reconciliation</p>
        </div>
        <div className="rounded-xl border border-accent/30 bg-accent/[0.04] p-5 lg:p-6">
          <div className="micro mb-4 text-accent">UrbanSync AI</div>
          <ol className="space-y-1.5">
            {ENGINE.map((e, i) => (
              <li key={e} className="text-[13.5px]">
                <span className="text-faint">{i > 0 && "↓ "}</span>
                <span className={i === ENGINE.length - 1 ? "font-medium text-accent" : ""}>{e}</span>
              </li>
            ))}
          </ol>
        </div>
        <div className="flex flex-col justify-between rounded-xl border border-line bg-panel p-5 sm:col-span-2 lg:col-span-1 lg:p-6">
          <div>
            <div className="micro mb-4">Result</div>
            <blockquote className="text-[17px] leading-relaxed font-medium">
              Instead of manually comparing thousands of records, urban data teams can focus their attention on the
              records that actually need review.
            </blockquote>
          </div>
          <p className="mt-6 text-[12.5px] text-faint">
            Every match carries an explainable confidence score; every discrepancy is queued with evidence. Source
            records are never modified.
          </p>
        </div>
      </div>
    </section>
  );
}

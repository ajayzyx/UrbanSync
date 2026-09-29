const CASES: { n: string; title: string; problem: string; compares: string; detects: string; review: string }[] = [
  { n: "01", title: "Cadastral Harmonization",
    problem: "A cadastral parcel and a municipal property boundary appear slightly different.",
    compares: "Geometry, area, centroid and attributes across both records.",
    detects: "Whether they represent the same real-world parcel, with a confidence score.",
    review: "Low-agreement pairs are queued with the evidence side by side." },
  { n: "02", title: "Revenue + Municipal Reconciliation",
    problem: "Revenue Khasra records and municipal property registers use different fields and identifiers.",
    compares: "Khasra_No / Property_ID, owner names and areas, mapped into one common schema.",
    detects: "Field-level disagreements between the linked records.",
    review: "A common spatial record with each source's value visible." },
  { n: "03", title: "GNSS / Ground Truth Validation",
    problem: "A surveyed GNSS point suggests an existing parcel boundary may be spatially offset.",
    compares: "Survey point locations against recorded parcel geometry.",
    detects: "Points that fall outside the boundary they reference.",
    review: "The spatial discrepancy, highlighted for a surveyor's decision." },
  { n: "04", title: "Building Footprint Verification",
    problem: "A building footprint extracted from imagery extends beyond the recorded parcel.",
    compares: "Footprint geometry against parcel and building records.",
    detects: "Overlaps and encroaching spatial relationships.",
    review: "Flagged relationships, parcel by parcel." },
  { n: "05", title: "Urban Change Detection",
    problem: "2025: no building footprint. 2026: a new structure appears in the update.",
    compares: "Two versions of the same layer, feature by feature.",
    detects: "New, modified and removed features with geometry deltas.",
    review: "A change list for verification before records are updated." },
  { n: "06", title: "Utility / Land Parcel Alignment",
    problem: "Utility network features may sit inconsistently against parcel and building layers.",
    compares: "Network geometry against parcel and building geometry.",
    detects: "Spatial relationships and possible inconsistencies.",
    review: "Candidate alignment issues for the utility team." },
];

export function UseCases() {
  return (
    <section className="border-y border-line bg-panel-2/60">
      <div className="mx-auto max-w-6xl px-4 py-20 md:px-6">
        <div className="micro mb-2 text-accent">Use cases</div>
        <h2 className="font-display text-[30px] font-medium tracking-tight md:text-[38px]">Where UrbanSync AI can help</h2>
        <p className="mt-3 max-w-2xl text-[14px] text-muted">
          Illustrative use cases for the harmonization workflow — demonstrated today with controlled test data, designed
          to integrate departmental sources.
        </p>
        <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {CASES.map((c) => (
            <article key={c.n} className="rounded-xl border border-line bg-panel p-5">
              <div className="micro text-accent">{c.n}</div>
              <h3 className="font-display mt-2 text-[17px] font-medium">{c.title}</h3>
              <dl className="mt-3 space-y-2.5 text-[12.5px] leading-relaxed">
                <div><dt className="micro mb-0.5">Problem</dt><dd className="text-muted">{c.problem}</dd></div>
                <div><dt className="micro mb-0.5">UrbanSync compares</dt><dd className="text-muted">{c.compares}</dd></div>
                <div><dt className="micro mb-0.5">It detects</dt><dd className="text-muted">{c.detects}</dd></div>
                <div><dt className="micro mb-0.5">You review</dt><dd className="text-muted">{c.review}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

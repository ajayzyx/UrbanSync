// MapLibre v6 runs its worker as an ES module next to a shared chunk; serve both from /public so
// the map works under Turbopack and fully offline.
import { copyFileSync, mkdirSync } from "node:fs";

const src = "node_modules/maplibre-gl/dist";
mkdirSync("public/maplibre", { recursive: true });
for (const f of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) copyFileSync(`${src}/${f}`, `public/maplibre/${f}`);

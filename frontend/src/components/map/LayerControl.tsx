"use client";

import { useState } from "react";
import { Icon } from "../ui/Icon";
import { LAYER_META, type LayerKey } from "./layers";

export function LayerControl({ visible, onToggle }: { visible: Record<LayerKey, boolean>; onToggle: (k: LayerKey) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setOpen((o) => !o)} aria-expanded={open}
        className="inline-flex items-center gap-2 rounded-lg border border-line-2 bg-panel/95 px-3 py-2 text-[13px] hover:border-accent/50">
        <Icon name="layers" /> Layers
      </button>
      {open && (
        <div className="absolute top-full left-0 z-20 mt-1 w-72 rounded-lg border border-line-2 bg-panel p-2 shadow-xl shadow-black/10">
          {LAYER_META.filter((l) => l.key !== "parcels").map((l) => (
            <label key={l.key} className="flex cursor-pointer items-start gap-2.5 rounded-md px-2 py-1.5 hover:bg-black/[0.03]">
              <input type="checkbox" checked={visible[l.key]} onChange={() => onToggle(l.key)} className="mt-0.5 accent-[#0f766e]" />
              <span>
                <span className="block text-[13px]">{l.label}</span>
                <span className="block text-[11.5px] text-faint">{l.hint}</span>
              </span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

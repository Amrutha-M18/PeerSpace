"use client";

import { Check, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CatalogItem, Selections } from "@/types/profile";
import { PROFICIENCY_LEVELS } from "./proficiency";

type Props = {
  title: string;
  description: string;
  items: CatalogItem[];
  selected: Selections;
  onChange: (next: Selections) => void;
  /** Show a proficiency dropdown in selected tiles (skills). Interests have no level. */
  withLevels?: boolean;
  /** Highlight selected tiles that still have no level (after a failed save). */
  showMissing?: boolean;
  emptyText: string;
};

/** Compact grid of tiles: click a tile to select it, then pick a proficiency inside it. */
export function SelectionGrid({
  title, description, items, selected, onChange, withLevels = true, showMissing, emptyText,
}: Props) {
  const count = Object.keys(selected).length;

  function toggle(id: number) {
    const next = { ...selected };
    if (id in next) delete next[id];
    else next[id] = null; // selected, but no proficiency yet
    onChange(next);
  }

  function setLevel(id: number, level: number) {
    onChange({ ...selected, [id]: level });
  }

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4 sm:p-5">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-neutral-900">{title}</h2>
          <p className="text-sm text-neutral-500">{description}</p>
        </div>
        <span className="shrink-0 text-xs text-neutral-500">{count} selected</span>
      </div>

      {items.length === 0 ? (
        <p className="rounded-lg bg-neutral-50 px-3 py-4 text-center text-sm text-neutral-500">{emptyText}</p>
      ) : (
        <ul className="grid grid-cols-2 items-start gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {items.map((item) => {
            const isSelected = item.id in selected;
            const level = selected[item.id] ?? null;
            const missing = withLevels && isSelected && level === null && showMissing;

            return (
              <li
                key={item.id}
                className={cn(
                  "rounded-lg border p-2 transition-colors",
                  isSelected
                    ? "border-neutral-800 bg-neutral-800 text-neutral-50"
                    : "border-neutral-200 bg-neutral-50 text-neutral-800 hover:border-neutral-400 hover:bg-white",
                  missing && "ring-2 ring-neutral-400 ring-offset-1",
                )}
              >
                <button
                  type="button"
                  onClick={() => toggle(item.id)}
                  aria-pressed={isSelected}
                  title={isSelected ? `Remove ${item.name}` : `Add ${item.name}`}
                  className="flex w-full items-center justify-between gap-2 rounded text-left text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400"
                >
                  <span className="truncate">{item.name}</span>
                  {isSelected ? (
                    <Check className="size-3.5 shrink-0" aria-hidden="true" />
                  ) : (
                    <Plus className="size-3.5 shrink-0 text-neutral-400" aria-hidden="true" />
                  )}
                </button>

                {withLevels && isSelected && (
                  <select
                    aria-label={`Proficiency in ${item.name}`}
                    value={level ?? ""}
                    onChange={(e) => setLevel(item.id, Number(e.target.value))}
                    className={cn(
                      "mt-2 w-full rounded-md border border-neutral-300 bg-white px-2 py-1 text-xs text-neutral-900",
                      "focus:outline-none focus:ring-2 focus:ring-neutral-400",
                      level === null && "text-neutral-500",
                    )}
                  >
                    <option value="" disabled>
                      Choose level
                    </option>
                    {PROFICIENCY_LEVELS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

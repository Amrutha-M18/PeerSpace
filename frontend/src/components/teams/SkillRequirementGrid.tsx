"use client";

import { useState } from "react";
import { Check, Minus, Plus, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { PROFICIENCY_LEVELS } from "@/components/profile/proficiency";
import type { CatalogItem } from "@/types/profile";

/** A chosen skill: minimum level and how many members need it. */
export type Requirement = { level: number; count: number };

/** New requirements start at Intermediate (2); the owner can change it. */
export const DEFAULT_LEVEL = 2;
export type Requirements = Record<number, Requirement>;

type Props = {
  title: string;
  description: string;
  items: CatalogItem[];
  selected: Requirements;
  onChange: (next: Requirements) => void;
  /** Hard requirements also ask how many members need the skill. */
  withCount?: boolean;
  maxCount?: number;
  /** Skills already used in the other list (a skill is either hard or preferred). */
  takenIds?: Set<number>;
  takenLabel?: string;
};

/** Compact, searchable grid of skill tiles. Selecting a tile shows a level dropdown (and a count). */
export function SkillRequirementGrid({
  title, description, items, selected, onChange,
  withCount = false, maxCount = 20, takenIds = new Set(), takenLabel = "Used elsewhere",
}: Props) {
  const [search, setSearch] = useState("");
  const count = Object.keys(selected).length;
  const term = search.trim().toLowerCase();
  const visible = term ? items.filter((item) => item.name.toLowerCase().includes(term)) : items;

  function toggle(id: number) {
    const next = { ...selected };
    if (id in next) delete next[id];
    else next[id] = { level: DEFAULT_LEVEL, count: 1 };
    onChange(next);
  }

  function update(id: number, patch: Partial<Requirement>) {
    onChange({ ...selected, [id]: { ...selected[id], ...patch } });
  }

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4 sm:p-5">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-neutral-900">{title}</h2>
          <p className="text-sm text-neutral-500">{description}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-neutral-500">{count} selected</span>
          <label className="relative block">
            <span className="sr-only">Search {title.toLowerCase()}</span>
            <Search className="pointer-events-none absolute top-1/2 left-2 size-3.5 -translate-y-1/2 text-neutral-400" aria-hidden="true" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skills"
              className="h-8 w-40 rounded-md border border-neutral-300 bg-white pr-2 pl-7 text-sm text-neutral-900 placeholder:text-neutral-400 focus:ring-2 focus:ring-neutral-400 focus:outline-none"
            />
          </label>
        </div>
      </div>

      {items.length === 0 ? (
        <p className="rounded-lg bg-neutral-50 px-3 py-4 text-center text-sm text-neutral-500">
          No skills in the catalogue yet.
        </p>
      ) : visible.length === 0 ? (
        <p className="rounded-lg bg-neutral-50 px-3 py-4 text-center text-sm text-neutral-500">
          No skills match &ldquo;{search}&rdquo;.
        </p>
      ) : (
        <ul className="grid grid-cols-2 items-start gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {visible.map((item) => {
            const requirement = selected[item.id];
            const isSelected = requirement !== undefined;
            const taken = !isSelected && takenIds.has(item.id);

            return (
              <li
                key={item.id}
                className={cn(
                  "rounded-lg border p-2 transition-colors",
                  isSelected && "border-neutral-800 bg-neutral-800 text-neutral-50",
                  !isSelected && !taken && "border-neutral-200 bg-neutral-50 text-neutral-800 hover:border-neutral-400 hover:bg-white",
                  taken && "border-dashed border-neutral-200 bg-white text-neutral-400",
                )}
              >
                <button
                  type="button"
                  onClick={() => toggle(item.id)}
                  disabled={taken}
                  aria-pressed={isSelected}
                  title={taken ? `${item.name}: ${takenLabel}` : isSelected ? `Remove ${item.name}` : `Add ${item.name}`}
                  className="flex w-full items-center justify-between gap-2 rounded text-left text-sm font-medium focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none disabled:cursor-not-allowed"
                >
                  <span className="truncate">{item.name}</span>
                  {isSelected ? (
                    <Check className="size-3.5 shrink-0" aria-hidden="true" />
                  ) : taken ? null : (
                    <Plus className="size-3.5 shrink-0 text-neutral-400" aria-hidden="true" />
                  )}
                </button>
                {taken && <p className="mt-1 text-[11px] leading-tight">{takenLabel}</p>}

                {isSelected && (
                  <div className="mt-2 flex flex-col gap-1.5">
                    <select
                      aria-label={`Minimum level for ${item.name}`}
                      value={requirement.level}
                      onChange={(e) => update(item.id, { level: Number(e.target.value) })}
                      className="w-full rounded-md border border-neutral-300 bg-white px-2 py-1 text-xs text-neutral-900 focus:ring-2 focus:ring-neutral-400 focus:outline-none"
                    >
                      {PROFICIENCY_LEVELS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>

                    {withCount && (
                      <div className="flex items-center justify-between rounded-md bg-white px-1 py-0.5 text-neutral-900">
                        <button
                          type="button"
                          aria-label={`Fewer members needing ${item.name}`}
                          onClick={() => update(item.id, { count: Math.max(1, requirement.count - 1) })}
                          disabled={requirement.count <= 1}
                          className="flex size-6 items-center justify-center rounded text-neutral-700 hover:bg-neutral-100 disabled:opacity-30"
                        >
                          <Minus className="size-3" />
                        </button>
                        <span className="text-xs" aria-live="polite">
                          {requirement.count} {requirement.count === 1 ? "person" : "people"}
                        </span>
                        <button
                          type="button"
                          aria-label={`More members needing ${item.name}`}
                          onClick={() => update(item.id, { count: Math.min(maxCount, requirement.count + 1) })}
                          disabled={requirement.count >= maxCount}
                          className="flex size-6 items-center justify-center rounded text-neutral-700 hover:bg-neutral-100 disabled:opacity-30"
                        >
                          <Plus className="size-3" />
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

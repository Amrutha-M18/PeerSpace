"use client";

import { useState } from "react";
import { X } from "lucide-react";

type Props = {
  ownerName: string;
  names: string[];
  onChange: (next: string[]) => void;
  /** How many more names fit (capacity minus the owner and the names already added). */
  remaining: number;
};

/** People already in the team, by name only. The owner is always the first member. */
export function MemberNamesInput({ ownerName, names, onChange, remaining }: Props) {
  const [draft, setDraft] = useState("");
  const trimmed = draft.trim();
  const canAdd = trimmed.length > 0 && trimmed.length <= 100 && remaining > 0;

  function add() {
    if (!canAdd) return;
    onChange([...names, trimmed]);
    setDraft("");
  }

  return (
    <div className="grid gap-2">
      <ul className="flex flex-wrap gap-1.5" aria-label="Current members">
        <li className="rounded-full bg-neutral-800 px-3 py-1 text-xs font-medium text-neutral-50">
          {ownerName} <span className="text-neutral-400">· you, owner</span>
        </li>
        {names.map((name, index) => (
          <li
            key={`${name}-${index}`}
            className="flex items-center gap-1 rounded-full border border-neutral-300 bg-neutral-50 py-1 pr-1 pl-3 text-xs text-neutral-800"
          >
            {name}
            <button
              type="button"
              onClick={() => onChange(names.filter((_, i) => i !== index))}
              aria-label={`Remove ${name}`}
              className="flex size-4 items-center justify-center rounded-full text-neutral-500 hover:bg-neutral-200 hover:text-neutral-900"
            >
              <X className="size-3" />
            </button>
          </li>
        ))}
      </ul>

      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              add();
            }
          }}
          maxLength={100}
          disabled={remaining <= 0}
          placeholder={remaining > 0 ? "Add a member by name" : "Team is full"}
          aria-label="Member name"
          className="h-8 min-w-0 flex-1 rounded-md border border-neutral-300 bg-white px-2.5 text-sm text-neutral-900 placeholder:text-neutral-400 focus:ring-2 focus:ring-neutral-400 focus:outline-none disabled:bg-neutral-100"
        />
        <button
          type="button"
          onClick={add}
          disabled={!canAdd}
          className="h-8 rounded-md border border-neutral-300 bg-white px-3 text-sm font-medium text-neutral-800 hover:bg-neutral-50 disabled:opacity-40"
        >
          Add
        </button>
      </div>
      <p className="text-xs text-neutral-500">Names only: these people don&apos;t need a PeerSpace account.</p>
    </div>
  );
}

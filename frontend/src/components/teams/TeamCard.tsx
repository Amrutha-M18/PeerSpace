"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BadgeCheck, Check, CircleSlash, Clock, Crown, Info, Loader2, Lock, Send, Star, UserPlus, UsersRound, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { PROFICIENCY_LEVELS } from "@/components/profile/proficiency";
import type { Team } from "@/types/teams";

/** What the signed-in user can do with a team, shown on its button. */
export type JoinState =
  | "join"          // can ask to join
  | "pending"       // asked, waiting for the owner
  | "accepted"      // owner said yes
  | "rejected"      // owner said no
  | "owner"         // it's their team
  | "member"        // already in it
  | "in-other-team" // in a different team for this opportunity
  | "full"
  | "closed";       // the opportunity is over

const levelLabel = (level: number) => PROFICIENCY_LEVELS.find((l) => l.value === Math.min(level, 4))?.label ?? `Level ${level}`;

/** Must-haves the viewer doesn't meet yet (by name). */
export function missingMustHaves(team: Team, mySkills: Map<number, number>) {
  return team.hard_requirements.filter((r) => (mySkills.get(r.skill_id) ?? 0) < r.min_level).map((r) => r.name);
}

type Props = {
  team: Team;
  state: JoinState;
  mySkills: Map<number, number>; // skill_id -> level
  highlight?: boolean;
  pendingCount?: number; // owner only: requests waiting for them
  onJoin: (message: string) => Promise<void>;
  onWithdraw: () => Promise<void>;
};

/** Compact team card. Hover (or tap the info icon) to see the full team details. */
export function TeamCard({ team, state, mySkills, highlight, pendingCount, onJoin, onWithdraw }: Props) {
  const [hovered, setHovered] = useState(false);
  const [pinned, setPinned] = useState(false); // opened with the info button (touch screens)
  const [writing, setWriting] = useState(false); // the "add a note" step before sending
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const open = (hovered || pinned) && !writing;

  const owner = team.members.find((m) => m.role === "owner");
  const filled = team.capacity - team.open_slots;
  const missing = missingMustHaves(team, mySkills);
  const detailsId = `team-${team.id}-details`;

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
      setWriting(false);
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article
      className={cn(
        "relative flex flex-col gap-2.5 rounded-xl border bg-white p-3.5 transition-colors",
        highlight ? "border-neutral-800 ring-2 ring-neutral-300" : "border-neutral-200 hover:border-neutral-400",
        open && "z-20",
      )}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <header className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-neutral-900">{team.name}</h3>
          <p className="truncate text-xs text-neutral-500">by {owner?.name ?? "Unknown"}</p>
        </div>
        <button
          type="button"
          onClick={() => setPinned((p) => !p)}
          aria-expanded={open}
          aria-controls={detailsId}
          aria-label={`Details for ${team.name}`}
          className="flex size-7 shrink-0 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none"
        >
          <Info className="size-4" />
        </button>
      </header>

      {/* Slots: one dot per place, filled for taken places */}
      <div className="flex items-center gap-2 text-xs text-neutral-600">
        <UsersRound className="size-3.5 shrink-0 text-neutral-400" aria-hidden="true" />
        <span className="flex flex-wrap gap-0.5" aria-hidden="true">
          {Array.from({ length: team.capacity }, (_, i) => (
            <span key={i} className={cn("size-2 rounded-full", i < filled ? "bg-neutral-700" : "border border-neutral-300")} />
          ))}
        </span>
        <span>
          {filled}/{team.capacity} · {team.open_slots === 0 ? "Full" : `${team.open_slots} open`}
        </span>
      </div>

      {team.hard_requirements.length > 0 ? (
        <ul className="flex flex-wrap gap-1" aria-label="Must-have skills">
          {team.hard_requirements.slice(0, 3).map((r) => (
            <li key={r.skill_id} className="rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] text-neutral-700">
              {r.name}
            </li>
          ))}
          {team.hard_requirements.length > 3 && (
            <li className="px-1 py-0.5 text-[11px] text-neutral-500">+{team.hard_requirements.length - 3}</li>
          )}
        </ul>
      ) : (
        <p className="text-[11px] text-neutral-500">No must-have skills</p>
      )}

      {state === "join" && (
        missing.length === 0 ? (
          <p className="flex items-center gap-1 text-xs font-medium text-neutral-800">
            <BadgeCheck className="size-3.5" aria-hidden="true" /> You meet every must-have
          </p>
        ) : (
          <p className="truncate text-xs text-neutral-500" title={`Missing: ${missing.join(", ")}`}>
            Missing: {missing.join(", ")}
          </p>
        )
      )}

      {/* Join step: optional note, then send */}
      {writing && (
        <div className="grid gap-1.5">
          <label htmlFor={`note-${team.id}`} className="text-xs text-neutral-600">
            Note for {owner?.name.split(" ")[0] ?? "the owner"} (optional)
          </label>
          <textarea
            id={`note-${team.id}`}
            rows={2}
            maxLength={500}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="What would you bring to the team?"
            className="resize-none rounded-lg border border-neutral-300 px-2 py-1 text-xs text-neutral-900 placeholder:text-neutral-400 focus:ring-2 focus:ring-neutral-400 focus:outline-none"
          />
        </div>
      )}

      <div className="mt-auto flex items-center gap-1.5 pt-0.5">
        <JoinButton
          state={state}
          busy={busy}
          writing={writing}
          pendingCount={pendingCount}
          onClick={() => (writing ? run(() => onJoin(note.trim())) : setWriting(true))}
        />
        {writing && (
          <button type="button" onClick={() => setWriting(false)} className="h-7 rounded-lg px-2 text-xs text-neutral-600 hover:bg-neutral-100">
            Cancel
          </button>
        )}
        {state === "pending" && (
          <button
            type="button"
            onClick={() => run(onWithdraw)}
            disabled={busy}
            aria-label={`Withdraw request to ${team.name}`}
            title="Withdraw request"
            className="flex size-7 items-center justify-center rounded-lg border border-neutral-300 text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 disabled:opacity-40"
          >
            <X className="size-3.5" />
          </button>
        )}
      </div>
      {error && <p role="alert" className="text-xs text-destructive">{error}</p>}

      {/* Hover card with everything about the team */}
      <div
        id={detailsId}
        role="region"
        aria-label={`${team.name} details`}
        hidden={!open}
        className="absolute inset-x-0 top-full z-30 mt-1.5 grid max-h-96 gap-3 overflow-y-auto rounded-xl border border-neutral-200 bg-white p-3.5 text-sm shadow-lg"
      >
        {team.description && <p className="text-neutral-700">{team.description}</p>}

        <div className="grid gap-1">
          <h4 className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Members</h4>
          <ul className="grid gap-1">
            {team.members.map((m) => (
              <li key={m.id} className="flex items-center gap-2">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-neutral-200 text-[11px] font-medium text-neutral-700">
                  {m.name.charAt(0).toUpperCase()}
                </span>
                {m.user_id ? (
                  <Link href={`/users/${m.user_id}`} className="truncate text-neutral-900 hover:underline">{m.name}</Link>
                ) : (
                  <span className="truncate text-neutral-900">{m.name}</span>
                )}
                {m.role === "owner" && <Crown className="size-3.5 shrink-0 text-neutral-500" aria-label="Owner" />}
                {!m.user_id && <span className="text-[11px] text-neutral-400">not on PeerSpace</span>}
              </li>
            ))}
            {Array.from({ length: team.open_slots }, (_, i) => (
              <li key={`open-${i}`} className="flex items-center gap-2 text-neutral-400">
                <span className="size-6 shrink-0 rounded-full border border-dashed border-neutral-300" />
                Open place
              </li>
            ))}
          </ul>
        </div>

        {team.hard_requirements.length > 0 && (
          <div className="grid gap-1">
            <h4 className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Must have</h4>
            <ul className="grid gap-1">
              {team.hard_requirements.map((r) => {
                const met = (mySkills.get(r.skill_id) ?? 0) >= r.min_level;
                return (
                  <li key={r.skill_id} className="flex items-center gap-2">
                    {met ? (
                      <Check className="size-3.5 shrink-0 text-neutral-900" aria-label="You have this" />
                    ) : (
                      <CircleSlash className="size-3.5 shrink-0 text-neutral-400" aria-label="You don't have this yet" />
                    )}
                    <span className="text-neutral-900">{r.name}</span>
                    <span className="text-xs text-neutral-500">
                      {levelLabel(r.min_level)}+ · {r.count} {r.count === 1 ? "person" : "people"}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {team.soft_requirements.length > 0 && (
          <div className="grid gap-1">
            <h4 className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Nice to have</h4>
            <ul className="flex flex-wrap gap-1">
              {team.soft_requirements.map((r) => (
                <li key={r.skill_id} className="inline-flex items-center gap-1 rounded-full border border-neutral-200 px-2 py-0.5 text-xs text-neutral-700">
                  <Star className="size-3 text-neutral-400" aria-hidden="true" />
                  {r.name} <span className="text-neutral-400">{levelLabel(r.min_level)}+</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </article>
  );
}

const BUTTONS: Record<JoinState, { label: string; Icon: React.ComponentType<{ className?: string }>; active?: boolean }> = {
  join: { label: "Join", Icon: UserPlus, active: true },
  pending: { label: "Requested", Icon: Clock },
  accepted: { label: "Accepted", Icon: Check },
  rejected: { label: "Declined", Icon: CircleSlash },
  owner: { label: "Your team", Icon: Crown },
  member: { label: "Member", Icon: Check },
  "in-other-team": { label: "In another team", Icon: Lock },
  full: { label: "Team full", Icon: Lock },
  closed: { label: "Closed", Icon: Lock },
};

/** One button per team; its text always says where the user stands. */
function JoinButton({ state, busy, writing, pendingCount, onClick }: {
  state: JoinState; busy: boolean; writing: boolean; pendingCount?: number; onClick: () => void;
}) {
  const { label, Icon, active } = BUTTONS[state];
  if (!active) {
    return (
      <span
        className={cn(
          "inline-flex h-7 items-center gap-1 rounded-lg border px-2.5 text-xs font-medium",
          state === "pending" || state === "accepted" || state === "owner" || state === "member"
            ? "border-neutral-800 bg-neutral-100 text-neutral-900"
            : "border-neutral-200 bg-neutral-50 text-neutral-500",
        )}
        aria-label={`Status: ${label}`}
      >
        <Icon className="size-3.5" />
        {label}
        {state === "owner" && pendingCount ? <span className="text-neutral-500">· {pendingCount} {pendingCount === 1 ? "request" : "requests"}</span> : null}
      </span>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={busy}
      className="inline-flex h-7 items-center gap-1 rounded-lg bg-neutral-900 px-2.5 text-xs font-medium text-white transition-colors hover:bg-neutral-700 disabled:opacity-60"
    >
      {busy ? <Loader2 className="size-3.5 animate-spin" /> : writing ? <Send className="size-3.5" /> : <Icon className="size-3.5" />}
      {writing ? "Send request" : label}
    </button>
  );
}

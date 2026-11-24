"use client";

import { useState } from "react";
import Link from "next/link";
import { BadgeCheck, Check, CircleAlert, Loader2, Minus, Star, UserCheck, UserX, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { PROFICIENCY_LEVELS } from "@/components/profile/proficiency";
import { timeAgo } from "@/lib/format";
import type { Applicant } from "@/types/teams";

export const levelLabel = (level: number) =>
  level <= 0 ? "None" : PROFICIENCY_LEVELS.find((l) => l.value === Math.min(level, 4))?.label ?? `Level ${level}`;

type Props = {
  applicant: Applicant;
  position: number; // 1-based place in the current sort order
  teamFull: boolean;
  onAccept: () => Promise<void>;
  onDecline: () => Promise<void>;
};

/** One pending request, as the team owner sees it: who they are and how they fit the team. */
export function ApplicantCard({ applicant: a, position, teamFull, onAccept, onDecline }: Props) {
  const [busy, setBusy] = useState<"accept" | "decline" | null>(null);
  const [error, setError] = useState("");

  async function run(which: "accept" | "decline", action: () => Promise<void>) {
    setBusy(which);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setBusy(null);
    }
  }

  return (
    <article className="grid gap-3 rounded-xl border border-neutral-200 bg-white p-4 sm:grid-cols-[1fr_auto] sm:gap-x-5">
      {/* Who */}
      <div className="flex min-w-0 items-start gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-neutral-200 text-sm font-medium text-neutral-700">
          {a.name.charAt(0).toUpperCase()}
        </span>
        <div className="min-w-0">
          <p className="flex flex-wrap items-baseline gap-x-2">
            <Link href={`/users/${a.user_id}`} className="font-semibold text-neutral-900 hover:underline">{a.name}</Link>
            <span className="text-xs text-neutral-500">#{position} · asked {timeAgo(a.requested_at)}</span>
          </p>
          {a.eligible ? (
            <p className="mt-0.5 flex items-center gap-1 text-xs font-medium text-neutral-800">
              <BadgeCheck className="size-3.5" aria-hidden="true" /> Meets every must-have
            </p>
          ) : (
            <p className="mt-0.5 flex items-center gap-1 text-xs text-neutral-600">
              <CircleAlert className="size-3.5" aria-hidden="true" /> Missing must-have: {a.missing_must_haves.join(", ")}
            </p>
          )}
          {a.message && (
            <p className="mt-2 border-l-2 border-neutral-200 pl-2 text-sm text-neutral-700">{a.message}</p>
          )}
        </div>
      </div>

      {/* Score from the matching module */}
      <div className="flex items-center gap-3 sm:row-span-2 sm:flex-col sm:items-end sm:justify-between">
        <div className="flex items-baseline gap-1 sm:flex-col sm:items-end sm:gap-0">
          <span className="text-2xl font-semibold text-neutral-900 tabular-nums">{Math.round(a.score)}</span>
          <span className="text-xs text-neutral-500">match score</span>
        </div>
        <div className="hidden h-1.5 w-24 overflow-hidden rounded-full bg-neutral-200 min-[420px]:block" aria-hidden="true">
          <div className="h-full rounded-full bg-neutral-800" style={{ width: `${Math.min(a.score, 100)}%` }} />
        </div>
        <div className="ml-auto flex gap-1.5 sm:ml-0">
          <button
            type="button"
            onClick={() => run("decline", onDecline)}
            disabled={busy !== null}
            className="inline-flex h-8 items-center gap-1 rounded-lg border border-neutral-300 px-2.5 text-xs font-medium text-neutral-800 hover:bg-neutral-100 disabled:opacity-50"
          >
            {busy === "decline" ? <Loader2 className="size-3.5 animate-spin" /> : <UserX className="size-3.5" aria-hidden="true" />}
            Decline
          </button>
          <button
            type="button"
            onClick={() => run("accept", onAccept)}
            disabled={busy !== null || teamFull}
            title={teamFull ? "The team is full. Remove a member first" : undefined}
            className="inline-flex h-8 items-center gap-1 rounded-lg bg-neutral-900 px-2.5 text-xs font-medium text-white hover:bg-neutral-700 disabled:opacity-40"
          >
            {busy === "accept" ? <Loader2 className="size-3.5 animate-spin" /> : <UserCheck className="size-3.5" aria-hidden="true" />}
            Accept
          </button>
        </div>
      </div>

      {/* Skill compatibility: each of the team's skills against the applicant's level */}
      <div className="grid gap-2 sm:col-start-1">
        {a.skill_checks.length > 0 && (
          <ul className="grid gap-1 sm:grid-cols-2" aria-label="Skill compatibility">
            {a.skill_checks.map((c) => (
              <li key={c.skill_id} className="flex min-w-0 items-center gap-1.5 text-xs">
                {c.meets ? (
                  <Check className="size-3.5 shrink-0 text-neutral-900" aria-label="Meets" />
                ) : c.user_level > 0 ? (
                  <Minus className="size-3.5 shrink-0 text-neutral-500" aria-label="Below the level" />
                ) : (
                  <X className="size-3.5 shrink-0 text-neutral-400" aria-label="Doesn't have it" />
                )}
                <span className={cn("truncate", c.meets ? "font-medium text-neutral-900" : "text-neutral-600")}>{c.name}</span>
                <span className="shrink-0 text-neutral-500">
                  {levelLabel(c.user_level)} / {levelLabel(c.required_level)}+
                </span>
                {c.must_have && <span className="shrink-0 rounded bg-neutral-100 px-1 text-[10px] text-neutral-600">must</span>}
                {c.in_focus && <Star className="size-3 shrink-0 fill-neutral-700 text-neutral-700" aria-label="In focus" />}
                {c.team_covers && !c.in_focus && (
                  <span className="shrink-0 text-[10px] text-neutral-400" title="A current member already has this, so it counts for less">
                    team has it
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
        {(a.other_skills.length > 0 || a.interests.length > 0) && (
          <div className="flex flex-wrap items-center gap-1 text-[11px] text-neutral-600">
            {a.other_skills.slice(0, 6).map((s) => (
              <span key={s.skill_id} className="rounded-full border border-neutral-200 px-2 py-0.5">
                {s.name} <span className="text-neutral-400">{levelLabel(s.level)}</span>
              </span>
            ))}
            {a.interests.length > 0 && (
              <span className="px-1 text-neutral-500">Interests: {a.interests.slice(0, 4).join(", ")}</span>
            )}
          </div>
        )}
        {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
      </div>
    </article>
  );
}

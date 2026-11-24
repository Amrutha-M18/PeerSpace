"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BookOpen, CalendarDays, ChevronRight, CodeXml, ExternalLink, GraduationCap, Heart, Mountain, Plus,
  Sparkles, Trophy, UserRound, UsersRound, type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { capitalize, dateRange, isOver } from "@/lib/format";
import type { FeedItem } from "@/types/opportunity";

export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  hackathon: CodeXml,
  "course project": GraduationCap,
  "study group": BookOpen,
  trek: Mountain,
  sport: Trophy,
  other: Sparkles,
};

const cardBase = "flex h-full flex-col rounded-xl border bg-white p-4";

/** One opportunity in the dashboard feed. Clicking anywhere on it opens the opportunity's page with its teams. */
export function OpportunityCard({ opportunity: o }: { opportunity: FeedItem }) {
  const Icon = CATEGORY_ICONS[o.category] ?? Sparkles;
  const over = isOver(o.starts_on, o.ends_on);
  const teamText = !o.is_team_based
    ? "Individual"
    : o.team_size
      ? `Teams of up to ${o.team_size}`
      : "Any team size";

  return (
    <article className={cn(cardBase, "relative gap-3 border-neutral-200 transition-colors hover:border-neutral-400 has-[a:focus-visible]:ring-2 has-[a:focus-visible]:ring-neutral-400", over && "opacity-70")}>
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-700">
          <Icon className="size-3.5" aria-hidden="true" />
          {capitalize(o.category)}
        </span>
        {over ? (
          <span className="text-xs text-neutral-500">Ended</span>
        ) : o.match_score > 0 ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-neutral-800" title="Fits your interests">
            <Heart className="size-3.5 fill-neutral-800" aria-hidden="true" />
            For you
          </span>
        ) : null}
      </div>

      <div>
        <h3 className="line-clamp-2 font-semibold leading-snug text-neutral-900">
          {/* The ::after covers the whole card, so the card itself is the link. */}
          <Link href={`/opportunities/${o.id}`} className="outline-none after:absolute after:inset-0 after:rounded-xl">
            {o.title}
          </Link>
        </h3>
        {o.organizer && <p className="mt-0.5 truncate text-xs text-neutral-500">by {o.organizer}</p>}
      </div>

      {o.description && <p className="line-clamp-2 text-sm text-neutral-600">{o.description}</p>}

      <ul className="grid gap-1 text-xs text-neutral-600">
        <li className="flex items-center gap-1.5">
          <CalendarDays className="size-3.5 shrink-0 text-neutral-400" aria-hidden="true" />
          {dateRange(o.starts_on, o.ends_on)}
        </li>
        <li className="flex items-center gap-1.5">
          {o.is_team_based ? (
            <UsersRound className="size-3.5 shrink-0 text-neutral-400" aria-hidden="true" />
          ) : (
            <UserRound className="size-3.5 shrink-0 text-neutral-400" aria-hidden="true" />
          )}
          {teamText}
          {o.is_team_based && o.team_count > 0 && (
            <span className="text-neutral-400">
              · {o.team_count} {o.team_count === 1 ? "team" : "teams"}, {o.open_team_count} open
            </span>
          )}
        </li>
      </ul>

      {o.matched_interests.length > 0 && (
        <ul className="flex flex-wrap gap-1" aria-label="Matches your interests">
          {o.matched_interests.slice(0, 3).map((name) => (
            <li key={name} className="rounded-full border border-neutral-200 px-2 py-0.5 text-[11px] text-neutral-700">
              {name}
            </li>
          ))}
          {o.matched_interests.length > 3 && (
            <li className="px-1 py-0.5 text-[11px] text-neutral-500">+{o.matched_interests.length - 3}</li>
          )}
        </ul>
      )}

      <div className="mt-auto flex items-center justify-between gap-2 pt-1">
        {o.is_team_based && !over ? (
          <Link
            href={`/teams/new?opportunity=${o.id}`}
            className="relative z-10 inline-flex h-7 items-center gap-1 rounded-lg bg-neutral-900 px-2.5 text-xs font-medium text-white transition-colors hover:bg-neutral-700"
          >
            <Plus className="size-3.5" aria-hidden="true" />
            Create team
          </Link>
        ) : (
          <span />
        )}
        <span className="ml-auto inline-flex items-center gap-0.5 text-xs font-medium text-neutral-500">
          {o.is_team_based ? "View teams" : "Details"}
          <ChevronRight className="size-3.5" aria-hidden="true" />
        </span>
        {o.official_url && (
          <a
            href={o.official_url}
            target="_blank"
            rel="noreferrer"
            aria-label={`Official page for ${o.title}`}
            className="relative z-10 inline-flex size-7 items-center justify-center rounded-lg text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-neutral-900"
          >
            <ExternalLink className="size-3.5" />
          </a>
        )}
      </div>
    </article>
  );
}

/** Grey placeholder shown while the feed loads. */
export function OpportunityCardSkeleton() {
  return (
    <div className={cn(cardBase, "animate-pulse gap-3 border-neutral-200")} aria-hidden="true">
      <div className="h-4 w-24 rounded-full bg-neutral-200" />
      <div className="grid gap-1.5">
        <div className="h-4 w-4/5 rounded bg-neutral-200" />
        <div className="h-3 w-1/3 rounded bg-neutral-100" />
      </div>
      <div className="grid gap-1.5">
        <div className="h-3 w-full rounded bg-neutral-100" />
        <div className="h-3 w-2/3 rounded bg-neutral-100" />
      </div>
      <div className="mt-auto h-7 w-24 rounded-lg bg-neutral-200" />
    </div>
  );
}

/** A ghost card: clicking it opens the Opportunity Creation page. */
export function AddOpportunityCard() {
  const router = useRouter();
  return (
    <button
      type="button"
      onClick={() => router.push("/opportunities/new")}
      className={cn(
        cardBase,
        "group relative min-h-48 items-center justify-center gap-2 border-dashed border-neutral-300 bg-neutral-50 text-center transition-colors hover:border-neutral-500 hover:bg-white focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none",
      )}
    >
      {/* faint skeleton lines behind, so it reads as "a card that isn't there yet" */}
      <span className="pointer-events-none absolute inset-4 grid content-start gap-2 opacity-60" aria-hidden="true">
        <span className="h-4 w-20 rounded-full bg-neutral-200/70" />
        <span className="h-4 w-3/4 rounded bg-neutral-200/70" />
        <span className="h-3 w-full rounded bg-neutral-100" />
        <span className="h-3 w-1/2 rounded bg-neutral-100" />
      </span>
      <span className="relative flex size-10 items-center justify-center rounded-full border border-neutral-300 bg-white text-neutral-700 transition-colors group-hover:border-neutral-800 group-hover:bg-neutral-800 group-hover:text-white">
        <Plus className="size-5" aria-hidden="true" />
      </span>
      <span className="relative text-sm font-medium text-neutral-900">Add an opportunity</span>
      <span className="relative text-xs text-neutral-500">Hackathon, project, trek… anything people can join</span>
    </button>
  );
}

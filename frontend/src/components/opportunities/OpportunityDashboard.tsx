"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Heart, LayoutGrid, Search, SearchX, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api/client";
import { getOpportunityFeed } from "@/lib/api/opportunities";
import { getProfile } from "@/lib/api/profile";
import { capitalize } from "@/lib/format";
import { OPPORTUNITY_CATEGORIES, type FeedItem, type OpportunityCategory } from "@/types/opportunity";
import { AddOpportunityCard, CATEGORY_ICONS, OpportunityCard, OpportunityCardSkeleton } from "./OpportunityCard";

const SEARCH_DELAY_MS = 250;
const grid = "grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3";

/** Searchable feed of opportunities; the ones that fit the user's interests come first. */
export function OpportunityDashboard() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState(""); // `search`, once the user stops typing
  const [category, setCategory] = useState<OpportunityCategory | null>(null);
  const [includePast, setIncludePast] = useState(false);
  const [feed, setFeed] = useState<FeedItem[] | null>(null); // null while loading
  const [error, setError] = useState("");
  const [interests, setInterests] = useState<string[] | null>(null);

  useEffect(() => {
    getProfile()
      .then((profile) => setInterests(profile.hobbies.map((h) => h.name)))
      .catch(() => setInterests([]));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => setQuery(search.trim()), SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    let current = true; // ignore answers to older searches
    getOpportunityFeed({ q: query || undefined, category: category ?? undefined, include_past: includePast || undefined })
      .then((items) => {
        if (!current) return;
        setFeed(items);
        setError("");
      })
      .catch((err) => {
        if (!current) return;
        setFeed([]);
        setError(err instanceof ApiError ? err.message : "Could not load opportunities");
      });
    return () => {
      current = false;
    };
  }, [query, category, includePast]);

  // Show the loading skeleton again whenever the filters change.
  const [shown, setShown] = useState({ query, category, includePast });
  if (shown.query !== query || shown.category !== category || shown.includePast !== includePast) {
    setShown({ query, category, includePast });
    setFeed(null);
  }

  const forYou = feed?.filter((o) => o.match_score > 0) ?? [];
  const others = feed?.filter((o) => o.match_score === 0) ?? [];
  const filtering = Boolean(query || category);

  return (
    <main className="flex-1 bg-neutral-100 px-4 py-6 sm:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold text-neutral-900">Opportunities</h1>
          <p className="text-sm text-neutral-500">
            {interests === null
              ? "Find something to join, or start a team."
              : interests.length > 0
                ? `Picked for your interests: ${interests.slice(0, 4).join(", ")}${interests.length > 4 ? "…" : ""}`
                : "Find something to join, or start a team."}
          </p>
        </header>

        {/* Search and filters */}
        <div className="flex flex-col gap-3 rounded-xl border border-neutral-200 bg-white p-3 sm:p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <label className="relative flex-1">
              <span className="sr-only">Search opportunities</span>
              <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-neutral-400" aria-hidden="true" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by title, description or organizer"
                className="h-9 w-full rounded-lg border border-neutral-300 bg-white pr-8 pl-8 text-sm text-neutral-900 placeholder:text-neutral-400 focus:ring-2 focus:ring-neutral-400 focus:outline-none [&::-webkit-search-cancel-button]:hidden"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  aria-label="Clear search"
                  className="absolute top-1/2 right-1.5 flex size-6 -translate-y-1/2 items-center justify-center rounded text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900"
                >
                  <X className="size-3.5" />
                </button>
              )}
            </label>
            <label className="flex shrink-0 items-center gap-2 text-sm text-neutral-700">
              <input
                type="checkbox"
                checked={includePast}
                onChange={(e) => setIncludePast(e.target.checked)}
                className="size-4 accent-neutral-800"
              />
              Show past ones
            </label>
          </div>

          <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-0.5" role="group" aria-label="Filter by category">
            <CategoryChip label="All" Icon={LayoutGrid} active={category === null} onClick={() => setCategory(null)} />
            {OPPORTUNITY_CATEGORIES.map((c) => (
              <CategoryChip
                key={c}
                label={capitalize(c)}
                Icon={CATEGORY_ICONS[c]}
                active={category === c}
                onClick={() => setCategory(category === c ? null : c)}
              />
            ))}
          </div>
        </div>

        {interests !== null && interests.length === 0 && (
          <p className="flex items-center gap-2 rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm text-neutral-600">
            <Heart className="size-4 shrink-0 text-neutral-400" aria-hidden="true" />
            <span>
              <Link href="/profile" className="font-medium text-neutral-900 underline underline-offset-2">
                Add interests to your profile
              </Link>{" "}
              to see opportunities picked for you first.
            </span>
          </p>
        )}

        {error && (
          <p role="alert" className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        {feed === null ? (
          <section aria-busy="true" aria-label="Loading opportunities" className={grid}>
            {Array.from({ length: 6 }, (_, i) => <OpportunityCardSkeleton key={i} />)}
          </section>
        ) : feed.length === 0 ? (
          <section className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-sm text-neutral-600">
              <SearchX className="size-4 text-neutral-400" aria-hidden="true" />
              {filtering ? "No opportunities match your search." : "No opportunities yet. Be the first to add one."}
            </div>
            <div className={grid}>
              <AddOpportunityCard />
            </div>
          </section>
        ) : (
          <>
            {forYou.length > 0 && (
              <FeedSection title="Picked for you" count={forYou.length} hint="Matches your interests">
                {forYou.map((o) => <OpportunityCard key={o.id} opportunity={o} />)}
                {others.length === 0 && <AddOpportunityCard />}
              </FeedSection>
            )}
            {others.length > 0 && (
              <FeedSection title={forYou.length > 0 ? "More opportunities" : filtering ? "Results" : "All opportunities"} count={others.length}>
                {others.map((o) => <OpportunityCard key={o.id} opportunity={o} />)}
                <AddOpportunityCard />
              </FeedSection>
            )}
          </>
        )}
      </div>
    </main>
  );
}

function FeedSection({ title, count, hint, children }: { title: string; count: number; hint?: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-2.5">
      <div className="flex items-baseline gap-2">
        <h2 className="text-base font-semibold text-neutral-900">{title}</h2>
        <span className="text-xs text-neutral-500">
          {count}
          {hint && ` · ${hint}`}
        </span>
      </div>
      <div className={grid}>{children}</div>
    </section>
  );
}

function CategoryChip({ label, Icon, active, onClick }: {
  label: string; Icon: React.ComponentType<{ className?: string }>; active: boolean; onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none",
        active
          ? "border-neutral-800 bg-neutral-800 text-neutral-50"
          : "border-neutral-200 bg-neutral-50 text-neutral-700 hover:border-neutral-400 hover:bg-white",
      )}
    >
      <Icon className="size-3.5" />
      {label}
    </button>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft, CalendarDays, CircleCheck, ExternalLink, Loader2, Plus, Sparkles, UserRound, UsersRound, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api/client";
import { getOpportunity } from "@/lib/api/opportunities";
import { getProfile } from "@/lib/api/profile";
import { getMyRequests, getRankedRequests, getTeams, requestToJoin, withdrawRequest } from "@/lib/api/teams";
import { capitalize, dateRange, isOver } from "@/lib/format";
import { useAuth } from "@/providers/AuthProvider";
import type { JoinRequest } from "@/types/join-reqeust";
import type { Opportunity } from "@/types/opportunity";
import type { Team } from "@/types/teams";
import { TeamCard, missingMustHaves, type JoinState } from "@/components/teams/TeamCard";
import { CATEGORY_ICONS } from "./OpportunityCard";

type Props = {
  opportunityId: number;
  created?: "team" | "opportunity"; // just made something: say so at the top
  highlightTeamId?: number;
};

/** /opportunities/[id]: the opportunity, and every team formed for it. */
export function OpportunityTeamsView({ opportunityId, created, highlightTeamId }: Props) {
  const { user } = useAuth(); // (app)/layout.tsx guarantees a signed-in user
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [requests, setRequests] = useState<JoinRequest[]>([]); // mine, newest first
  const [mySkills, setMySkills] = useState(new Map<number, number>());
  const [pendingForMe, setPendingForMe] = useState(0); // requests waiting on my own team
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [banner, setBanner] = useState(created);

  useEffect(() => {
    Promise.all([getOpportunity(opportunityId), getTeams(opportunityId), getMyRequests(opportunityId), getProfile()])
      .then(([opp, teamList, mine, profile]) => {
        setOpportunity(opp);
        setTeams(teamList);
        setRequests(mine);
        setMySkills(new Map(profile.skills.map((s) => [s.skill_id, s.level])));
        const owned = teamList.find((t) => t.owner_id === profile.id);
        if (owned) getRankedRequests(owned.id).then((r) => setPendingForMe(r.length)).catch(() => {});
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this opportunity"))
      .finally(() => setLoading(false));
  }, [opportunityId]);

  const myTeam = teams.find((t) => t.members.some((m) => m.user_id === user?.id));
  const over = opportunity ? isOver(opportunity.starts_on, opportunity.ends_on) : false;

  function stateFor(team: Team): JoinState {
    if (team.owner_id === user?.id) return "owner";
    if (team === myTeam) return "member";
    const latest = requests.find((r) => r.team_id === team.id);
    if (latest?.status === "pending" || latest?.status === "accepted" || latest?.status === "rejected") return latest.status;
    if (myTeam) return "in-other-team";
    if (over) return "closed";
    if (team.open_slots === 0) return "full";
    return "join";
  }

  // My team first, then open teams I fit, then other open teams, then full ones.
  const sorted = useMemo(() => {
    const rank = (t: Team) =>
      t === myTeam ? 0 : t.open_slots === 0 ? 3 : missingMustHaves(t, mySkills).length === 0 ? 1 : 2;
    return [...teams].sort((a, b) => rank(a) - rank(b) || b.open_slots - a.open_slots || a.id - b.id);
  }, [teams, myTeam, mySkills]);

  async function join(team: Team, message: string) {
    const request = await requestToJoin(team.id, message);
    setRequests((current) => [request, ...current]);
  }

  async function withdraw(team: Team) {
    await withdrawRequest(team.id);
    setRequests((current) => current.filter((r) => !(r.team_id === team.id && r.status === "pending")));
  }

  if (loading) {
    return (
      <main className="flex flex-1 items-center justify-center bg-neutral-100">
        <Loader2 className="size-5 animate-spin text-neutral-500" aria-label="Loading" />
      </main>
    );
  }

  if (!opportunity) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3 bg-neutral-100 px-4 text-center">
        <p className="text-sm text-neutral-700">{error || "Opportunity not found"}</p>
        <Link href="/opportunities" className="text-sm font-medium text-neutral-900 underline underline-offset-2">Back to opportunities</Link>
      </main>
    );
  }

  const Icon = CATEGORY_ICONS[opportunity.category] ?? Sparkles;
  const canCreate = opportunity.is_team_based && !over && !myTeam;
  const openTeams = teams.filter((t) => t.open_slots > 0).length;

  return (
    <main className="flex-1 bg-neutral-100 px-4 py-6 sm:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-4">
        <Link href="/opportunities" className="inline-flex w-fit items-center gap-1 text-sm text-neutral-600 hover:text-neutral-900">
          <ArrowLeft className="size-4" aria-hidden="true" /> All opportunities
        </Link>

        {banner && (
          <div role="status" className="flex items-center gap-2 rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800">
            <CircleCheck className="size-4 shrink-0" aria-hidden="true" />
            <span className="flex-1">
              {banner === "team" ? "Team created. It's now listed below." : "Opportunity added. Start the first team for it, or share it with friends."}
            </span>
            <button type="button" onClick={() => setBanner(undefined)} aria-label="Dismiss" className="rounded p-0.5 text-neutral-500 hover:bg-neutral-100">
              <X className="size-4" />
            </button>
          </div>
        )}

        {/* About the opportunity */}
        <section className="flex flex-col gap-3 rounded-xl border border-neutral-200 bg-white p-4 sm:flex-row sm:items-start sm:justify-between sm:p-5">
          <div className="flex min-w-0 flex-col gap-2">
            <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-700">
              <Icon className="size-3.5" aria-hidden="true" />
              {capitalize(opportunity.category)}
              {over && <span className="text-neutral-500">· Ended</span>}
            </span>
            <div>
              <h1 className="text-2xl font-semibold text-neutral-900">{opportunity.title}</h1>
              {opportunity.organizer && <p className="text-sm text-neutral-500">by {opportunity.organizer}</p>}
            </div>
            {opportunity.description && <p className="max-w-3xl text-sm whitespace-pre-line text-neutral-700">{opportunity.description}</p>}
            <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-neutral-600">
              <li className="flex items-center gap-1.5">
                <CalendarDays className="size-3.5 text-neutral-400" aria-hidden="true" />
                {dateRange(opportunity.starts_on, opportunity.ends_on)}
              </li>
              <li className="flex items-center gap-1.5">
                {opportunity.is_team_based ? (
                  <UsersRound className="size-3.5 text-neutral-400" aria-hidden="true" />
                ) : (
                  <UserRound className="size-3.5 text-neutral-400" aria-hidden="true" />
                )}
                {!opportunity.is_team_based ? "Individual" : opportunity.team_size ? `Teams of up to ${opportunity.team_size}` : "Any team size"}
              </li>
              {opportunity.official_url && (
                <li>
                  <a href={opportunity.official_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-medium text-neutral-800 hover:underline">
                    Official page <ExternalLink className="size-3" aria-hidden="true" />
                  </a>
                </li>
              )}
            </ul>
          </div>
          {canCreate ? (
            <Link
              href={`/teams/new?opportunity=${opportunity.id}`}
              className="inline-flex h-9 shrink-0 items-center justify-center gap-1.5 rounded-lg bg-neutral-900 px-3 text-sm font-medium text-white hover:bg-neutral-700"
            >
              <Plus className="size-4" aria-hidden="true" /> Create team
            </Link>
          ) : myTeam ? (
            <span className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-lg border border-neutral-300 px-3 text-sm text-neutral-700">
              <UsersRound className="size-4" aria-hidden="true" /> You&apos;re in {myTeam.name}
            </span>
          ) : null}
        </section>

        {/* Teams */}
        {!opportunity.is_team_based ? (
          <p className="rounded-xl border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-600">
            Everyone takes part on their own in this one, so there are no teams.
          </p>
        ) : (
          <section className="flex flex-col gap-2.5" aria-label="Teams">
            <div className="flex items-baseline gap-2">
              <h2 className="text-base font-semibold text-neutral-900">Teams</h2>
              <span className="text-xs text-neutral-500">
                {teams.length} {teams.length === 1 ? "team" : "teams"} · {openTeams} open
              </span>
              <span className="ml-auto hidden text-xs text-neutral-400 sm:inline">Hover a team for details</span>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {sorted.map((team) => (
                <TeamCard
                  key={team.id}
                  team={team}
                  state={stateFor(team)}
                  mySkills={mySkills}
                  highlight={team.id === highlightTeamId}
                  pendingCount={team.owner_id === user?.id ? pendingForMe : undefined}
                  onJoin={(message) => join(team, message)}
                  onWithdraw={() => withdraw(team)}
                />
              ))}
              {canCreate && (
                <Link
                  href={`/teams/new?opportunity=${opportunity.id}`}
                  className={cn(
                    "group flex min-h-40 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-neutral-300 bg-neutral-50 p-4 text-center transition-colors hover:border-neutral-500 hover:bg-white",
                  )}
                >
                  <span className="flex size-9 items-center justify-center rounded-full border border-neutral-300 bg-white text-neutral-700 transition-colors group-hover:border-neutral-800 group-hover:bg-neutral-800 group-hover:text-white">
                    <Plus className="size-4" aria-hidden="true" />
                  </span>
                  <span className="text-sm font-medium text-neutral-900">{teams.length ? "Start your own team" : "Create the first team"}</span>
                  <span className="text-xs text-neutral-500">Pick the skills you need and invite people</span>
                </Link>
              )}
            </div>
            {teams.length === 0 && !canCreate && <p className="text-sm text-neutral-500">No teams were formed.</p>}
          </section>
        )}
      </div>
    </main>
  );
}

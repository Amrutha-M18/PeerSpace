"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowDownWideNarrow, ArrowLeft, ArrowUpNarrowWide, Check, Crown, Inbox, Loader2, Star, Target, UserMinus, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api/client";
import { getOpportunity } from "@/lib/api/opportunities";
import {
  acceptRequest, declineRequest, getApplicants, getMyRequests, getTeam, getTeams, removeMember, requestToJoin,
  withdrawRequest,
} from "@/lib/api/teams";
import { capitalize, isOver } from "@/lib/format";
import { useAuth } from "@/providers/AuthProvider";
import type { JoinRequest } from "@/types/join-reqeust";
import type { Opportunity } from "@/types/opportunity";
import type { Applicant, ApplicantOrder, Team } from "@/types/teams";
import { ApplicantCard, levelLabel } from "./ApplicantCard";
import { JoinButton, joinStateFor } from "./TeamCard";

/** "Non-decreasing score" is what was asked for; the owner can flip it. */
const DEFAULT_ORDER: ApplicantOrder = "lowest_first";

/** /teams/[id]: everyone sees the team; only the owner sees (and answers) join requests. */
export function TeamDetailsView({ teamId }: { teamId: number }) {
  const { user } = useAuth(); // (app)/layout.tsx guarantees a signed-in user
  const [team, setTeam] = useState<Team | null>(null);
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [myTeamHere, setMyTeamHere] = useState<Team | undefined>(); // my team in this opportunity, if any
  const [myRequest, setMyRequest] = useState<JoinRequest | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getTeam(teamId)
      .then(async (t) => {
        const [opp, teams, mine] = await Promise.all([
          getOpportunity(t.opportunity_id), getTeams(t.opportunity_id), getMyRequests(t.opportunity_id),
        ]);
        setTeam(t);
        setOpportunity(opp);
        setMyTeamHere(teams.find((x) => x.members.some((m) => m.user_id === user?.id)));
        setMyRequest(mine.find((r) => r.team_id === t.id));
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this team"))
      .finally(() => setLoading(false));
  }, [teamId, user?.id]);

  if (loading) {
    return (
      <main className="flex flex-1 items-center justify-center bg-neutral-100">
        <Loader2 className="size-5 animate-spin text-neutral-500" aria-label="Loading" />
      </main>
    );
  }
  if (!team || !opportunity) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3 bg-neutral-100 px-4 text-center">
        <p className="text-sm text-neutral-700">{error || "Team not found"}</p>
        <Link href="/opportunities" className="text-sm font-medium text-neutral-900 underline underline-offset-2">Back to opportunities</Link>
      </main>
    );
  }

  const isOwner = team.owner_id === user?.id;
  const isMember = team.members.some((m) => m.user_id === user?.id);
  const owner = team.members.find((m) => m.role === "owner");
  const state = joinStateFor({
    team, userId: user?.id, myTeam: isMember ? team : myTeamHere, latest: myRequest,
    over: isOver(opportunity.starts_on, opportunity.ends_on),
  });

  return (
    <main className="flex-1 bg-neutral-100 px-4 py-6 sm:py-8">
      <div className="mx-auto flex max-w-5xl flex-col gap-4">
        <Link href={`/opportunities/${opportunity.id}`} className="inline-flex w-fit items-center gap-1 text-sm text-neutral-600 hover:text-neutral-900">
          <ArrowLeft className="size-4" aria-hidden="true" /> {opportunity.title}
        </Link>

        {/* Header */}
        <section className="flex flex-col gap-3 rounded-xl border border-neutral-200 bg-white p-4 sm:flex-row sm:items-start sm:justify-between sm:p-5">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className={cn(
                "rounded-full px-2 py-0.5 font-medium",
                team.status === "open" ? "bg-neutral-900 text-white" : "bg-neutral-200 text-neutral-700",
              )}>
                {team.status === "open" ? "Open" : "Full"}
              </span>
              <span className="text-neutral-500">
                {capitalize(opportunity.category)} · {opportunity.title}
              </span>
            </div>
            <h1 className="mt-1.5 text-2xl font-semibold text-neutral-900">{team.name}</h1>
            <p className="text-sm text-neutral-500">
              Owned by{" "}
              {owner?.user_id ? (
                <Link href={`/users/${owner.user_id}`} className="font-medium text-neutral-800 hover:underline">{owner.name}</Link>
              ) : (owner?.name ?? "Unknown")}
            </p>
            {team.description && <p className="mt-2 max-w-2xl text-sm whitespace-pre-line text-neutral-700">{team.description}</p>}
          </div>
          <ViewerAction
            state={state}
            onJoin={async (message) => setMyRequest(await requestToJoin(team.id, message))}
            onWithdraw={async () => {
              await withdrawRequest(team.id);
              setMyRequest(undefined);
            }}
          />
        </section>

        {/* Numbers */}
        <dl className="grid grid-cols-3 gap-3">
          {([["Capacity", team.capacity], ["Members", team.members.length], ["Available slots", team.open_slots]] as const).map(([label, value]) => (
            <div key={label} className="rounded-xl border border-neutral-200 bg-white px-4 py-3">
              <dt className="text-xs text-neutral-500">{label}</dt>
              <dd className="text-2xl font-semibold text-neutral-900 tabular-nums">{value}</dd>
            </div>
          ))}
        </dl>

        <div className="grid gap-4 lg:grid-cols-2">
          <MembersCard team={team} isOwner={isOwner} onChange={setTeam} />
          <SkillsCard team={team} />
        </div>

        {isOwner && <RequestsSection team={team} onTeamChange={setTeam} />}
      </div>
    </main>
  );
}

/** Join / Requested / Member … for whoever is looking at the page. */
function ViewerAction({ state, onJoin, onWithdraw }: {
  state: ReturnType<typeof joinStateFor>;
  onJoin: (message: string) => Promise<void>;
  onWithdraw: () => Promise<void>;
}) {
  const [writing, setWriting] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
      setWriting(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex shrink-0 flex-col gap-2 sm:w-64 sm:items-end">
      {writing && (
        <textarea
          rows={2}
          maxLength={500}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          aria-label="Note for the owner (optional)"
          placeholder="Note for the owner (optional)"
          className="w-full resize-none rounded-lg border border-neutral-300 px-2 py-1 text-xs text-neutral-900 placeholder:text-neutral-400 focus:ring-2 focus:ring-neutral-400 focus:outline-none"
        />
      )}
      <div className="flex items-center gap-1.5">
        {writing && (
          <button type="button" onClick={() => setWriting(false)} className="h-7 rounded-lg px-2 text-xs text-neutral-600 hover:bg-neutral-100">
            Cancel
          </button>
        )}
        <JoinButton
          state={state}
          busy={busy}
          writing={writing}
          onClick={() => (writing ? run(() => onJoin(note.trim())) : setWriting(true))}
        />
        {state === "pending" && (
          <button
            type="button"
            onClick={() => run(onWithdraw)}
            disabled={busy}
            aria-label="Withdraw request"
            title="Withdraw request"
            className="flex size-7 items-center justify-center rounded-lg border border-neutral-300 text-neutral-600 hover:bg-neutral-100 disabled:opacity-40"
          >
            <X className="size-3.5" />
          </button>
        )}
      </div>
      {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

function MembersCard({ team, isOwner, onChange }: { team: Team; isOwner: boolean; onChange: (t: Team) => void }) {
  const [confirming, setConfirming] = useState<number | null>(null); // member id waiting for "Remove?"
  const [error, setError] = useState("");

  async function remove(memberId: number) {
    setError("");
    try {
      onChange(await removeMember(team.id, memberId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove the member");
    }
    setConfirming(null);
  }

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4 sm:p-5" aria-label="Members">
      <h2 className="mb-3 text-base font-semibold text-neutral-900">
        Members <span className="text-xs font-normal text-neutral-500">{team.members.length} of {team.capacity}</span>
      </h2>
      <ul className="grid gap-2">
        {team.members.map((m) => (
          <li key={m.id} className="flex items-center gap-2.5">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-neutral-200 text-xs font-medium text-neutral-700">
              {m.name.charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              {m.user_id ? (
                <Link href={`/users/${m.user_id}`} className="truncate text-sm font-medium text-neutral-900 hover:underline">{m.name}</Link>
              ) : (
                <span className="truncate text-sm font-medium text-neutral-900">{m.name}</span>
              )}
              <p className="text-xs text-neutral-500">
                {m.role === "owner" ? "Owner" : "Member"}
                {!m.user_id && " · not on PeerSpace"}
              </p>
            </div>
            {m.role === "owner" && <Crown className="size-4 text-neutral-500" aria-hidden="true" />}
            {isOwner && m.role !== "owner" && (
              confirming === m.id ? (
                <span className="flex items-center gap-1">
                  <button type="button" onClick={() => remove(m.id)} className="h-7 rounded-lg bg-neutral-900 px-2 text-xs font-medium text-white hover:bg-neutral-700">
                    Remove
                  </button>
                  <button type="button" onClick={() => setConfirming(null)} className="h-7 rounded-lg px-2 text-xs text-neutral-600 hover:bg-neutral-100">
                    Keep
                  </button>
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirming(m.id)}
                  aria-label={`Remove ${m.name}`}
                  title={`Remove ${m.name}`}
                  className="flex size-7 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900"
                >
                  <UserMinus className="size-4" />
                </button>
              )
            )}
          </li>
        ))}
        {Array.from({ length: team.open_slots }, (_, i) => (
          <li key={`open-${i}`} className="flex items-center gap-2.5 text-sm text-neutral-400">
            <span className="size-8 shrink-0 rounded-full border border-dashed border-neutral-300" />
            Open place
          </li>
        ))}
      </ul>
      {error && <p role="alert" className="mt-2 text-xs text-destructive">{error}</p>}
    </section>
  );
}

function SkillsCard({ team }: { team: Team }) {
  return (
    <section className="grid content-start gap-4 rounded-xl border border-neutral-200 bg-white p-4 sm:p-5" aria-label="Skills">
      <div className="grid gap-2">
        <h2 className="text-base font-semibold text-neutral-900">Must-have skills</h2>
        {team.hard_requirements.length === 0 ? (
          <p className="text-sm text-neutral-500">None: anyone can join.</p>
        ) : (
          <ul className="grid gap-2.5">
            {team.hard_requirements.map((r) => {
              const found = Math.min(r.members_with_skill, r.count);
              return (
                <li key={r.skill_id} className="grid gap-1">
                  <div className="flex items-baseline justify-between gap-2 text-sm">
                    <span className="font-medium text-neutral-900">
                      {r.name} <span className="font-normal text-neutral-500">{levelLabel(r.min_level)}+</span>
                    </span>
                    <span className="flex items-center gap-1 text-xs text-neutral-600">
                      {found >= r.count && <Check className="size-3.5" aria-hidden="true" />}
                      {found} of {r.count} {r.count === 1 ? "person" : "people"} found
                    </span>
                  </div>
                  <div className="flex gap-0.5" aria-hidden="true">
                    {Array.from({ length: r.count }, (_, i) => (
                      <span key={i} className={cn("h-1.5 flex-1 rounded-full", i < found ? "bg-neutral-800" : "bg-neutral-200")} />
                    ))}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
      <div className="grid gap-2">
        <h2 className="text-base font-semibold text-neutral-900">Nice to have</h2>
        {team.soft_requirements.length === 0 ? (
          <p className="text-sm text-neutral-500">None listed.</p>
        ) : (
          <ul className="flex flex-wrap gap-1.5">
            {team.soft_requirements.map((r) => (
              <li key={r.skill_id} className="inline-flex items-center gap-1 rounded-full border border-neutral-200 px-2.5 py-1 text-xs text-neutral-700">
                <Star className="size-3 text-neutral-400" aria-hidden="true" />
                {r.name} <span className="text-neutral-400">{levelLabel(r.min_level)}+</span>
                {r.members_with_skill > 0 && <Check className="size-3 text-neutral-900" aria-label="The team has this" />}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

/** Owner only: pending requests, scored and sorted by the matching module. */
function RequestsSection({ team, onTeamChange }: { team: Team; onTeamChange: (t: Team) => void }) {
  const [order, setOrder] = useState<ApplicantOrder>(DEFAULT_ORDER);
  const [focus, setFocus] = useState<number[]>([]);
  const [applicants, setApplicants] = useState<Applicant[] | null>(null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0); // bump to reload after accept/decline
  const skills = [...team.hard_requirements, ...team.soft_requirements];

  useEffect(() => {
    let current = true;
    getApplicants(team.id, order, focus)
      .then((list) => {
        if (!current) return; // the owner changed the sort or focus meanwhile
        setApplicants(list);
        setError("");
      })
      .catch((err) => {
        if (current) setError(err instanceof ApiError ? err.message : "Could not load requests");
      });
    return () => {
      current = false;
    };
  }, [team.id, order, focus, version]);

  // Opened from "Your team · N requests" (…#requests): scroll here once the list has loaded.
  const loaded = applicants !== null;
  useEffect(() => {
    if (loaded && window.location.hash === "#requests") {
      document.getElementById("requests")?.scrollIntoView({ block: "start" });
    }
  }, [loaded]);

  const toggleFocus = (id: number) => setFocus((f) => (f.includes(id) ? f.filter((x) => x !== id) : [...f, id]));

  return (
    <section id="requests" className="flex scroll-mt-20 flex-col gap-3" aria-label="Join requests">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-neutral-900">
          Join requests {applicants && <span className="text-xs font-normal text-neutral-500">{applicants.length} pending · only you can see these</span>}
        </h2>
        <div className="inline-flex rounded-lg border border-neutral-300 bg-white p-0.5 text-xs" role="group" aria-label="Sort requests">
          {([
            ["lowest_first", "Lowest score first", ArrowUpNarrowWide],
            ["best_first", "Best match first", ArrowDownWideNarrow],
          ] as const).map(([value, label, Icon]) => (
            <button
              key={value}
              type="button"
              aria-pressed={order === value}
              onClick={() => setOrder(value)}
              className={cn(
                "inline-flex items-center gap-1 rounded-md px-2 py-1 font-medium",
                order === value ? "bg-neutral-900 text-white" : "text-neutral-700 hover:bg-neutral-100",
              )}
            >
              <Icon className="size-3.5" aria-hidden="true" /> {label}
            </button>
          ))}
        </div>
      </div>

      {skills.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="inline-flex items-center gap-1 text-neutral-600">
            <Target className="size-3.5" aria-hidden="true" /> Weigh more:
          </span>
          {skills.map((s) => (
            <button
              key={s.skill_id}
              type="button"
              aria-pressed={focus.includes(s.skill_id)}
              onClick={() => toggleFocus(s.skill_id)}
              className={cn(
                "rounded-full border px-2.5 py-0.5 font-medium transition-colors",
                focus.includes(s.skill_id)
                  ? "border-neutral-800 bg-neutral-800 text-white"
                  : "border-neutral-300 bg-white text-neutral-700 hover:border-neutral-500",
              )}
            >
              {s.name}
            </button>
          ))}
          <span className="text-neutral-400">Scores: must-haves decide eligibility; skills the team lacks count more; focused skills count double.</span>
        </div>
      )}

      {team.open_slots === 0 && (
        <p className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-600">
          The team is full. Remove a member to accept someone new.
        </p>
      )}
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

      {applicants === null ? (
        <div className="h-24 animate-pulse rounded-xl border border-neutral-200 bg-white" aria-busy="true" aria-label="Loading requests" />
      ) : applicants.length === 0 ? (
        <div className="flex items-center gap-2 rounded-xl border border-dashed border-neutral-300 bg-neutral-50 px-4 py-6 text-sm text-neutral-500">
          <Inbox className="size-4" aria-hidden="true" /> No pending requests right now.
        </div>
      ) : (
        <div className="grid gap-3">
          {applicants.map((a, i) => (
            <ApplicantCard
              key={a.request_id}
              applicant={a}
              position={i + 1}
              teamFull={team.open_slots === 0}
              onAccept={async () => {
                onTeamChange(await acceptRequest(team.id, a.request_id));
                setVersion((v) => v + 1); // scores change: the new member now covers skills
              }}
              onDecline={async () => {
                await declineRequest(team.id, a.request_id);
                setVersion((v) => v + 1);
              }}
            />
          ))}
        </div>
      )}
    </section>
  );
}

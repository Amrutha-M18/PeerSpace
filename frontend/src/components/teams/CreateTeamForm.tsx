"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { getSkillCatalog } from "@/lib/api/profile";
import { createTeam, getOpportunities } from "@/lib/api/teams";
import { useAuth } from "@/providers/AuthProvider";
import type { Opportunity } from "@/types/opportunity";
import type { CatalogItem } from "@/types/profile";
import { MemberNamesInput } from "./MemberNamesInput";
import { SkillRequirementGrid, type Requirements } from "./SkillRequirementGrid";

const MIN_CAPACITY = 2;
const MAX_CAPACITY = 20;
const DESCRIPTION_LIMIT = 300;

type Form = {
  opportunityId: string;
  name: string;
  description: string;
  capacity: number;
  members: string[];
  hard: Requirements;
  preferred: Requirements;
};

const emptyForm = (opportunityId = ""): Form => ({
  opportunityId, name: "", description: "", capacity: 4, members: [], hard: {}, preferred: {},
});


/** Everything that would stop the team from being created, in plain words. */
function problems(form: Form, skills: CatalogItem[], maxCapacity: number): string[] {
  const list: string[] = [];
  const skillName = (id: number) => skills.find((s) => s.id === id)?.name ?? `Skill ${id}`;
  if (!form.opportunityId) list.push("Choose the opportunity this team is for");
  if (!form.name.trim()) list.push("Give the team a name");
  if (1 + form.members.length > form.capacity) list.push("More members than the team's capacity");
  if (form.capacity > maxCapacity) list.push(`Teams for this opportunity can have at most ${maxCapacity} people`);
  const tooMany = Object.entries(form.hard)
    .filter(([, r]) => r.count > form.capacity)
    .map(([id]) => skillName(Number(id)));
  if (tooMany.length) list.push(`More people needed than the team's capacity for: ${tooMany.join(", ")}`);
  return list;
}

export function CreateTeamForm({ initialOpportunityId }: { initialOpportunityId?: string }) {
  const { user } = useAuth(); // (app)/layout.tsx guarantees a signed-in user

  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [skills, setSkills] = useState<CatalogItem[]>([]);
  const [form, setForm] = useState<Form>(() => emptyForm(initialOpportunityId ?? ""));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const router = useRouter();

  useEffect(() => {
    Promise.all([getOpportunities(), getSkillCatalog()])
      .then(([opps, catalog]) => {
        const teamBased = opps.filter((o) => o.is_team_based);
        setOpportunities(teamBased);
        setSkills(catalog);
        // Opened as /teams/new?opportunity=ID: fit the default capacity to that opportunity's limit.
        const limit = teamBased.find((o) => String(o.id) === initialOpportunityId)?.team_size;
        if (limit) setForm((current) => ({ ...current, capacity: Math.min(current.capacity, limit) }));
      })
      .catch((err) => setErrors([err instanceof ApiError ? err.message : "Could not load the form"]))
      .finally(() => setLoading(false));
  }, [initialOpportunityId]);

  const opportunity = opportunities.find((o) => String(o.id) === form.opportunityId);
  const maxCapacity = opportunity?.team_size ?? MAX_CAPACITY; // the opportunity can set a smaller limit
  const availableSlots = form.capacity - 1 - form.members.length;
  const hardIds = useMemo(() => new Set(Object.keys(form.hard).map(Number)), [form.hard]);
  const preferredIds = useMemo(() => new Set(Object.keys(form.preferred).map(Number)), [form.preferred]);

  function update(patch: Partial<Form>) {
    setForm((current) => ({ ...current, ...patch }));
    setErrors([]);
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const found = problems(form, skills, maxCapacity);
    if (found.length) {
      setErrors(found);
      return;
    }
    setSaving(true);
    setErrors([]);
    try {
      const team = await createTeam(Number(form.opportunityId), {
        name: form.name.trim(),
        description: form.description.trim() || null,
        capacity: form.capacity,
        default_members: form.members,
        hard_requirements: Object.entries(form.hard).map(([id, r]) => ({
          skill_id: Number(id), min_level: r.level, count: r.count,
        })),
        soft_requirements: Object.entries(form.preferred).map(([id, r]) => ({
          skill_id: Number(id), min_level: r.level,
        })),
      });
      // Go to the opportunity's page, where the new team is listed (and highlighted).
      router.push(`/opportunities/${team.opportunity_id}?created=team&team=${team.id}`);
      // (The button stays disabled while the next page loads.)
    } catch (err) {
      setErrors([err instanceof ApiError ? err.message : "Could not create the team"]);
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="flex flex-1 items-center justify-center bg-neutral-100">
        <Loader2 className="size-5 animate-spin text-neutral-500" aria-label="Loading" />
      </main>
    );
  }

  return (
    <main className="flex-1 bg-neutral-100 px-4 py-8">
      <form onSubmit={onSubmit} noValidate className="mx-auto flex max-w-4xl flex-col gap-4">
        <header>
          <h1 className="text-2xl font-semibold text-neutral-900">Create a team</h1>
          <p className="text-sm text-neutral-500">Describe your team and the skills you&apos;re looking for.</p>
        </header>

        {/* Basics */}
        <section className="grid gap-4 rounded-xl border border-neutral-200 bg-white p-4 sm:p-5">
          <div className="grid gap-1.5">
            <Label htmlFor="opportunity">Opportunity</Label>
            <select
              id="opportunity"
              value={form.opportunityId}
              onChange={(e) => {
                const chosen = opportunities.find((o) => String(o.id) === e.target.value);
                const limit = chosen?.team_size ?? MAX_CAPACITY;
                // Shrink the team to fit the opportunity's limit (but never below the people already added).
                update({ opportunityId: e.target.value, capacity: Math.max(Math.min(form.capacity, limit), 1 + form.members.length) });
              }}
              className="h-8 rounded-lg border border-neutral-300 bg-white px-2 text-sm text-neutral-900 focus:ring-2 focus:ring-neutral-400 focus:outline-none"
            >
              <option value="">{opportunities.length ? "Choose an opportunity" : "No opportunities yet"}</option>
              {opportunities.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.title} · {o.category}
                </option>
              ))}
            </select>
            <p className="text-xs text-neutral-500">
              Not listed?{" "}
              <Link href="/opportunities/new" className="font-medium text-neutral-800 underline underline-offset-2">
                Add the opportunity
              </Link>{" "}
              first.
            </p>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="team-name">Team name</Label>
            <Input id="team-name" value={form.name} maxLength={100} onChange={(e) => update({ name: e.target.value })} placeholder="e.g. Pixel Pushers" />
          </div>
          <div className="grid gap-1.5">
            <div className="flex items-baseline justify-between">
              <Label htmlFor="description">Short description</Label>
              <span className="text-xs text-neutral-500">{form.description.length}/{DESCRIPTION_LIMIT}</span>
            </div>
            <textarea
              id="description"
              rows={3}
              maxLength={DESCRIPTION_LIMIT}
              value={form.description}
              onChange={(e) => update({ description: e.target.value })}
              placeholder="What will the team build or do?"
              className="resize-none rounded-lg border border-neutral-300 bg-white px-2.5 py-1.5 text-sm text-neutral-900 placeholder:text-neutral-400 focus:ring-2 focus:ring-neutral-400 focus:outline-none"
            />
          </div>
        </section>

        {/* Size and members */}
        <section className="grid gap-4 rounded-xl border border-neutral-200 bg-white p-4 sm:grid-cols-[auto_1fr] sm:gap-6 sm:p-5">
          <div className="grid content-start gap-3">
            <div className="grid gap-1.5">
              <Label id="capacity-label">Total team capacity</Label>
              <div className="flex items-center gap-1" role="group" aria-labelledby="capacity-label">
                <button
                  type="button"
                  aria-label="Decrease capacity"
                  onClick={() => update({ capacity: Math.max(MIN_CAPACITY, Math.max(form.capacity - 1, 1 + form.members.length)) })}
                  disabled={form.capacity <= Math.max(MIN_CAPACITY, 1 + form.members.length)}
                  className="flex size-8 items-center justify-center rounded-md border border-neutral-300 text-neutral-700 hover:bg-neutral-50 disabled:opacity-30"
                >
                  <Minus className="size-3.5" />
                </button>
                <span className="w-10 text-center text-lg font-semibold text-neutral-900" aria-live="polite">{form.capacity}</span>
                <button
                  type="button"
                  aria-label="Increase capacity"
                  onClick={() => update({ capacity: Math.min(maxCapacity, form.capacity + 1) })}
                  disabled={form.capacity >= maxCapacity}
                  className="flex size-8 items-center justify-center rounded-md border border-neutral-300 text-neutral-700 hover:bg-neutral-50 disabled:opacity-30"
                >
                  <Plus className="size-3.5" />
                </button>
              </div>
              <p className="text-xs text-neutral-500">
                Including you. {MIN_CAPACITY}–{maxCapacity} people{opportunity?.team_size ? " (this opportunity's limit)" : ""}.
              </p>
            </div>
            <div className="rounded-lg bg-neutral-100 px-3 py-2">
              <p className="text-xs text-neutral-500">Available slots</p>
              <p className="text-2xl font-semibold text-neutral-900" aria-live="polite">{availableSlots}</p>
              <p className="text-xs text-neutral-500">{availableSlots === 0 ? "The team will start full" : "Open for others to join"}</p>
            </div>
          </div>

          <div className="grid content-start gap-1.5">
            <Label>Current members</Label>
            <MemberNamesInput
              ownerName={user?.name ?? "You"}
              names={form.members}
              onChange={(members) => update({ members })}
              remaining={availableSlots}
            />
          </div>
        </section>

        <SkillRequirementGrid
          title="Hard skill requirements"
          description="Must-haves: a minimum level, and how many members need each skill."
          items={skills}
          selected={form.hard}
          onChange={(hard) => update({ hard })}
          withCount
          maxCount={form.capacity}
          takenIds={preferredIds}
          takenLabel="In preferred skills"
        />

        <SkillRequirementGrid
          title="Preferred skills"
          description="Nice to have. They help rank people but don't rule anyone out."
          items={skills}
          selected={form.preferred}
          onChange={(preferred) => update({ preferred })}
          takenIds={hardIds}
          takenLabel="In hard requirements"
        />

        <div className="flex flex-col-reverse items-stretch gap-2 sm:flex-row sm:items-start sm:justify-end sm:gap-3">
          {errors.length > 0 && (
            <ul className="text-sm text-destructive sm:text-right" role="alert">
              {errors.map((error) => <li key={error}>{error}</li>)}
            </ul>
          )}
          <Button type="submit" disabled={saving} size="lg" className="px-4">
            {saving && <Loader2 className="animate-spin" />}
            {saving ? "Creating…" : "Create team"}
          </Button>
        </div>
      </form>
    </main>
  );
}

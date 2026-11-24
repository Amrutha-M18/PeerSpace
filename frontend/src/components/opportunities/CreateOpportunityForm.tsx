"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api/client";
import { createOpportunity } from "@/lib/api/opportunities";
import { capitalize } from "@/lib/format";
import { OPPORTUNITY_CATEGORIES, type OpportunityCategory } from "@/types/opportunity";

const MIN_TEAM_SIZE = 2;
const MAX_TEAM_SIZE = 20;
const DESCRIPTION_LIMIT = 2000;

type Form = {
  title: string;
  category: OpportunityCategory | "";
  organizer: string;
  description: string;
  startsOn: string; // "YYYY-MM-DD" from <input type="date">, or ""
  endsOn: string;
  officialUrl: string;
  isTeamBased: boolean;
  limitTeamSize: boolean;
  teamSize: number;
};

const emptyForm = (): Form => ({
  title: "", category: "", organizer: "", description: "", startsOn: "", endsOn: "",
  officialUrl: "", isTeamBased: true, limitTeamSize: true, teamSize: 4,
});

/** Everything that would stop the opportunity from being saved, in plain words. */
function problems(form: Form): string[] {
  const list: string[] = [];
  if (!form.title.trim()) list.push("Give the opportunity a title");
  if (!form.category) list.push("Choose a category");
  if (form.startsOn && form.endsOn && form.endsOn < form.startsOn) list.push("The end date can't be before the start date");
  const url = form.officialUrl.trim();
  if (url && !/^https?:\/\/\S+\.\S+/i.test(url)) list.push("The official link should start with http:// or https://");
  return list;
}

export function CreateOpportunityForm() {
  const [form, setForm] = useState<Form>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const router = useRouter();

  function update(patch: Partial<Form>) {
    setForm((current) => ({ ...current, ...patch }));
    setErrors([]);
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const found = problems(form);
    if (found.length) {
      setErrors(found);
      return;
    }
    setSaving(true);
    try {
      const opportunity = await createOpportunity({
        title: form.title.trim(),
        category: form.category as OpportunityCategory,
        organizer: form.organizer.trim() || null,
        description: form.description.trim() || null,
        starts_on: form.startsOn || null,
        ends_on: form.endsOn || null,
        official_url: form.officialUrl.trim() || null,
        is_team_based: form.isTeamBased,
        team_size: form.isTeamBased && form.limitTeamSize ? form.teamSize : null,
      });
      router.push(`/opportunities/${opportunity.id}?created=opportunity`);
      // (The button stays disabled while the next page loads.)
    } catch (err) {
      setErrors([err instanceof ApiError ? err.message : "Could not save the opportunity"]);
      setSaving(false);
    }
  }

  return (
    <main className="flex-1 bg-neutral-100 px-4 py-8">
      <form onSubmit={onSubmit} noValidate className="mx-auto flex max-w-3xl flex-col gap-4">
        <header>
          <h1 className="text-2xl font-semibold text-neutral-900">Add an opportunity</h1>
          <p className="text-sm text-neutral-500">A hackathon, course project, trek or anything else people can join.</p>
        </header>

        {/* What */}
        <section className="grid gap-4 rounded-xl border border-neutral-200 bg-white p-4 sm:p-5">
          <div className="grid gap-1.5">
            <Label htmlFor="title">Title</Label>
            <Input id="title" value={form.title} maxLength={200} onChange={(e) => update({ title: e.target.value })} placeholder="e.g. Campus Hackathon 2026" />
          </div>

          <fieldset className="grid gap-1.5">
            <legend className="mb-1.5 text-sm font-medium text-neutral-900">Category</legend>
            <div className="flex flex-wrap gap-2">
              {OPPORTUNITY_CATEGORIES.map((category) => (
                <label
                  key={category}
                  className={cn(
                    "cursor-pointer rounded-full border px-3 py-1 text-sm transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-neutral-400",
                    form.category === category
                      ? "border-neutral-800 bg-neutral-800 text-neutral-50"
                      : "border-neutral-300 bg-neutral-50 text-neutral-800 hover:border-neutral-400 hover:bg-white",
                  )}
                >
                  <input
                    type="radio"
                    name="category"
                    value={category}
                    checked={form.category === category}
                    onChange={() => update({ category })}
                    className="sr-only"
                  />
                  {capitalize(category)}
                </label>
              ))}
            </div>
          </fieldset>

          <div className="grid gap-1.5">
            <Label htmlFor="organizer">
              Organizer <span className="font-normal text-neutral-500">(optional)</span>
            </Label>
            <Input id="organizer" value={form.organizer} maxLength={200} onChange={(e) => update({ organizer: e.target.value })} placeholder="e.g. Coding Club" />
          </div>

          <div className="grid gap-1.5">
            <div className="flex items-baseline justify-between">
              <Label htmlFor="description">
                Description <span className="font-normal text-neutral-500">(optional)</span>
              </Label>
              <span className="text-xs text-neutral-500">{form.description.length}/{DESCRIPTION_LIMIT}</span>
            </div>
            <textarea
              id="description"
              rows={4}
              maxLength={DESCRIPTION_LIMIT}
              value={form.description}
              onChange={(e) => update({ description: e.target.value })}
              placeholder="What is it about, who is it for, and what will people do?"
              className="resize-y rounded-lg border border-neutral-300 bg-white px-2.5 py-1.5 text-sm text-neutral-900 placeholder:text-neutral-400 focus:ring-2 focus:ring-neutral-400 focus:outline-none"
            />
          </div>
        </section>

        {/* When and where */}
        <section className="grid gap-4 rounded-xl border border-neutral-200 bg-white p-4 sm:grid-cols-2 sm:p-5">
          <div className="grid gap-1.5">
            <Label htmlFor="starts-on">
              Starts on <span className="font-normal text-neutral-500">(optional)</span>
            </Label>
            <Input id="starts-on" type="date" value={form.startsOn} onChange={(e) => update({ startsOn: e.target.value })} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="ends-on">
              Ends on <span className="font-normal text-neutral-500">(optional)</span>
            </Label>
            <Input id="ends-on" type="date" value={form.endsOn} min={form.startsOn || undefined} onChange={(e) => update({ endsOn: e.target.value })} />
          </div>
          <div className="grid gap-1.5 sm:col-span-2">
            <Label htmlFor="official-url">
              Official link <span className="font-normal text-neutral-500">(optional)</span>
            </Label>
            <Input id="official-url" type="url" inputMode="url" value={form.officialUrl} maxLength={500} onChange={(e) => update({ officialUrl: e.target.value })} placeholder="https://…" />
          </div>
        </section>

        {/* Teams */}
        <section className="grid gap-4 rounded-xl border border-neutral-200 bg-white p-4 sm:p-5">
          <label className="flex cursor-pointer items-start justify-between gap-4">
            <span>
              <span className="block text-sm font-medium text-neutral-900">People join in teams</span>
              <span className="block text-sm text-neutral-500">
                {form.isTeamBased ? "Students can create teams for this opportunity." : "Everyone takes part on their own; no teams can be created."}
              </span>
            </span>
            <input
              type="checkbox"
              role="switch"
              checked={form.isTeamBased}
              onChange={(e) => update({ isTeamBased: e.target.checked })}
              className="peer sr-only"
            />
            <span
              aria-hidden="true"
              className="relative mt-0.5 h-5 w-9 shrink-0 rounded-full bg-neutral-300 transition-colors peer-checked:bg-neutral-800 peer-focus-visible:ring-2 peer-focus-visible:ring-neutral-400 after:absolute after:top-0.5 after:left-0.5 after:size-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-4"
            />
          </label>

          {form.isTeamBased && (
            <div className="grid gap-1.5 border-t border-neutral-100 pt-4">
              <Label id="team-size-label">Max team size</Label>
              <div className="flex flex-wrap items-center gap-4">
                <div className={cn("flex items-center gap-1", !form.limitTeamSize && "opacity-40")} role="group" aria-labelledby="team-size-label">
                  <button
                    type="button"
                    aria-label="Smaller teams"
                    onClick={() => update({ teamSize: Math.max(MIN_TEAM_SIZE, form.teamSize - 1) })}
                    disabled={!form.limitTeamSize || form.teamSize <= MIN_TEAM_SIZE}
                    className="flex size-8 items-center justify-center rounded-md border border-neutral-300 text-neutral-700 hover:bg-neutral-50 disabled:opacity-30"
                  >
                    <Minus className="size-3.5" />
                  </button>
                  <span className="w-10 text-center text-lg font-semibold text-neutral-900" aria-live="polite">
                    {form.limitTeamSize ? form.teamSize : "–"}
                  </span>
                  <button
                    type="button"
                    aria-label="Bigger teams"
                    onClick={() => update({ teamSize: Math.min(MAX_TEAM_SIZE, form.teamSize + 1) })}
                    disabled={!form.limitTeamSize || form.teamSize >= MAX_TEAM_SIZE}
                    className="flex size-8 items-center justify-center rounded-md border border-neutral-300 text-neutral-700 hover:bg-neutral-50 disabled:opacity-30"
                  >
                    <Plus className="size-3.5" />
                  </button>
                </div>
                <label className="flex items-center gap-2 text-sm text-neutral-700">
                  <input
                    type="checkbox"
                    checked={!form.limitTeamSize}
                    onChange={(e) => update({ limitTeamSize: !e.target.checked })}
                    className="size-4 accent-neutral-800"
                  />
                  No size limit
                </label>
              </div>
              <p className="text-xs text-neutral-500">
                {form.limitTeamSize
                  ? `Teams can have ${MIN_TEAM_SIZE}–${form.teamSize} people, including the team owner.`
                  : "Team owners choose any size up to 20."}
              </p>
            </div>
          )}
        </section>

        <div className="flex flex-col-reverse items-stretch gap-2 sm:flex-row sm:items-start sm:justify-end sm:gap-3">
          {errors.length > 0 && (
            <ul className="text-sm text-destructive sm:text-right" role="alert">
              {errors.map((error) => <li key={error}>{error}</li>)}
            </ul>
          )}
          <Button type="submit" disabled={saving} size="lg" className="px-4">
            {saving && <Loader2 className="animate-spin" />}
            {saving ? "Saving…" : "Add opportunity"}
          </Button>
        </div>
      </form>
    </main>
  );
}

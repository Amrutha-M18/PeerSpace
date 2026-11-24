"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { getInterestCatalog, getProfile, getSkillCatalog, saveProfile } from "@/lib/api/profile";
import { useAuth } from "@/providers/AuthProvider";
import type { CatalogItem, Profile, Selections } from "@/types/profile";
import { toUiLevel } from "./proficiency";
import { SelectionGrid } from "./SelectionGrid";

type FormState = { name: string; skills: Selections; interests: Selections };

function fromProfile(profile: Profile): FormState {
  return {
    name: profile.name,
    skills: Object.fromEntries(profile.skills.map((s) => [s.skill_id, toUiLevel(s.level)])),
    interests: Object.fromEntries(profile.hobbies.map((h) => [h.hobby_id, null])),
  };
}

/** Names of selected items that have no proficiency yet. */
function missingLevels(selected: Selections, catalog: CatalogItem[]): string[] {
  return catalog.filter((item) => item.id in selected && selected[item.id] === null).map((item) => item.name);
}

export function ProfileEditor() {
  const { user } = useAuth(); // (app)/layout.tsx guarantees a signed-in user

  const [skillCatalog, setSkillCatalog] = useState<CatalogItem[]>([]);
  const [interestCatalog, setInterestCatalog] = useState<CatalogItem[]>([]);
  const [email, setEmail] = useState("");
  const [saved, setSaved] = useState<FormState | null>(null); // last saved version, to detect changes
  const [form, setForm] = useState<FormState>({ name: "", skills: {}, interests: {} });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showMissing, setShowMissing] = useState(false);

  useEffect(() => {
    if (!user) return;
    Promise.all([getProfile(), getSkillCatalog(), getInterestCatalog()])
      .then(([profile, skills, interests]) => {
        const state = fromProfile(profile);
        setEmail(profile.email);
        setSkillCatalog(skills);
        setInterestCatalog(interests);
        setForm(state);
        setSaved(state);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load your profile"))
      .finally(() => setLoading(false));
  }, [user]);

  const changed = useMemo(() => JSON.stringify(form) !== JSON.stringify(saved), [form, saved]);

  function update(patch: Partial<FormState>) {
    setForm((current) => ({ ...current, ...patch }));
    setMessage(null);
  }

  async function onSave() {
    const missing = missingLevels(form.skills, skillCatalog);
    if (missing.length > 0) {
      setShowMissing(true);
      setError(`Choose a proficiency for: ${missing.join(", ")}`);
      return;
    }
    if (!form.name.trim()) {
      setError("Name can't be empty");
      return;
    }

    setError(null);
    setShowMissing(false);
    setSaving(true);
    try {
      const profile = await saveProfile({
        name: form.name.trim(),
        skills: Object.entries(form.skills).map(([id, level]) => ({ skill_id: Number(id), level: level as number })),
        hobbies: Object.keys(form.interests).map(Number),
      });
      const state = fromProfile(profile);
      setForm(state);
      setSaved(state);
      setMessage("Profile saved");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your profile");
    } finally {
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
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        <header>
          <h1 className="text-2xl font-semibold text-neutral-900">Your profile</h1>
          <p className="text-sm text-neutral-500">Pick your skills and interests so teams can find you.</p>
        </header>

        <section className="grid gap-4 rounded-xl border border-neutral-200 bg-white p-4 sm:grid-cols-2 sm:p-5">
          <div className="grid gap-1.5">
            <Label htmlFor="name">Name</Label>
            <Input id="name" value={form.name} maxLength={100} onChange={(e) => update({ name: e.target.value })} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" value={email} disabled />
          </div>
        </section>

        <SelectionGrid
          title="Skills"
          description="Select your skills, then choose a proficiency for each."
          items={skillCatalog}
          selected={form.skills}
          onChange={(skills) => update({ skills })}
          showMissing={showMissing}
          emptyText="No skills in the catalogue yet."
        />

        <SelectionGrid
          title="Interests"
          description="Sports, music, hobbies and anything else you enjoy. Pick as many as you like."
          items={interestCatalog}
          selected={form.interests}
          onChange={(interests) => update({ interests })}
          withLevels={false}
          emptyText="No interests in the catalogue yet."
        />

        <div className="flex flex-col-reverse items-stretch gap-2 sm:flex-row sm:items-center sm:justify-end sm:gap-3">
          {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
          {!error && message && <p className="text-sm text-neutral-600" role="status">{message}</p>}
          <Button onClick={onSave} disabled={saving || !changed} size="lg" className="px-4">
            {saving && <Loader2 className="animate-spin" />}
            {saving ? "Saving…" : "Save profile"}
          </Button>
        </div>
      </div>
    </main>
  );
}

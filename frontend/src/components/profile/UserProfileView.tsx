"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Pencil } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { getUserProfile } from "@/lib/api/profile";
import { useAuth } from "@/providers/AuthProvider";
import type { PublicProfile } from "@/types/profile";
import { PROFICIENCY_LEVELS, toUiLevel } from "./proficiency";

const MAX_LEVEL = PROFICIENCY_LEVELS.length;

function levelLabel(level: number) {
  return PROFICIENCY_LEVELS.find((l) => l.value === toUiLevel(level))?.label ?? "—";
}

/** Read-only profile of any user: name plus a table of skills and proficiency. */
export function UserProfileView({ userId }: { userId: string }) {
  const { user } = useAuth();
  const id = Number(userId);
  const validId = Number.isInteger(id) && id > 0;

  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [error, setError] = useState<string | null>(validId ? null : "User not found");

  useEffect(() => {
    if (!validId) return;
    getUserProfile(id)
      .then(setProfile)
      .catch((err) =>
        setError(
          err instanceof ApiError && (err.status === 404 || err.status === 422)
            ? "User not found"
            : err instanceof ApiError ? err.message : "Could not load this profile",
        ),
      );
  }, [id, validId]);

  if (error) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-2 px-4">
        <p className="text-base font-medium text-neutral-800">{error}</p>
        <Link href="/" className="text-sm text-neutral-500 underline underline-offset-4 hover:text-neutral-800">
          Back to home
        </Link>
      </main>
    );
  }

  if (!profile) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <Loader2 className="size-5 animate-spin text-neutral-500" aria-label="Loading" />
      </main>
    );
  }

  const isMe = user?.id === profile.id;

  return (
    <main className="flex-1 px-4 py-8">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        <header className="flex items-center justify-between gap-4 rounded-xl border border-neutral-200 bg-white p-5">
          <div className="flex items-center gap-3">
            <span className="flex size-12 items-center justify-center rounded-full bg-neutral-200 text-lg font-semibold text-neutral-700">
              {profile.name.charAt(0).toUpperCase()}
            </span>
            <h1 className="text-xl font-semibold text-neutral-900">{profile.name}</h1>
          </div>
          {isMe && (
            <Link href="/profile" className={buttonVariants({ variant: "outline" })}>
              <Pencil /> Edit profile
            </Link>
          )}
        </header>

        <section className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
          <h2 className="border-b border-neutral-200 px-5 py-3 text-base font-semibold text-neutral-900">
            Skills
          </h2>
          {profile.skills.length === 0 ? (
            <p className="px-5 py-6 text-sm text-neutral-500">No skills added yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-xs font-medium tracking-wide text-neutral-500 uppercase">
                <tr>
                  <th scope="col" className="px-5 py-2.5">Skill</th>
                  <th scope="col" className="px-5 py-2.5">Proficiency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {profile.skills.map((skill) => {
                  const level = toUiLevel(skill.level);
                  return (
                    <tr key={skill.skill_id}>
                      <td className="px-5 py-3 font-medium text-neutral-800">{skill.name}</td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <span className="flex gap-1" aria-hidden>
                            {Array.from({ length: MAX_LEVEL }, (_, i) => (
                              <span
                                key={i}
                                className={`h-1.5 w-5 rounded-full ${i < level ? "bg-neutral-700" : "bg-neutral-200"}`}
                              />
                            ))}
                          </span>
                          <span className="text-neutral-700">{levelLabel(skill.level)}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </main>
  );
}

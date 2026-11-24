"use client";

import Link from "next/link";
import { CalendarPlus, CircleUserRound, Plus } from "lucide-react";
import { useAuth } from "@/providers/AuthProvider";

/** Right side of the navbar when signed in: "Add opportunity", "Create team" and the profile icon. */
export function UserMenu() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="flex items-center gap-2">
      <Link
        href="/opportunities/new"
        aria-label="Add opportunity"
        className="inline-flex h-8 items-center gap-1 rounded-lg border border-neutral-300 px-2 text-sm font-medium text-neutral-800 transition-colors hover:bg-neutral-100 focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none sm:px-3"
      >
        <CalendarPlus className="size-4" aria-hidden="true" />
        <span className="hidden sm:inline">Add opportunity</span>
      </Link>
      <Link
        href="/teams/new"
        aria-label="Create team"
        className="inline-flex h-8 items-center gap-1 rounded-lg border border-neutral-300 px-2 text-sm font-medium text-neutral-800 transition-colors hover:bg-neutral-100 focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none sm:px-3"
      >
        <Plus className="size-4" aria-hidden="true" />
        <span className="hidden sm:inline">Create team</span>
      </Link>
      <Link
        href="/profile"
        aria-label="Your profile"
        title={user.name}
        className="flex size-9 items-center justify-center rounded-full text-neutral-700 transition-colors hover:bg-neutral-100 hover:text-neutral-900 focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none"
      >
        <CircleUserRound className="size-6" />
      </Link>
    </div>
  );
}

"use client";

import Link from "next/link";
import { CircleUserRound } from "lucide-react";
import { useAuth } from "@/providers/AuthProvider";

/** User icon on the right of the navbar. Shown only when signed in; opens the profile page. */
export function UserMenu() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <Link
      href="/profile"
      aria-label="Your profile"
      title={user.name}
      className="flex size-9 items-center justify-center rounded-full text-neutral-700 transition-colors hover:bg-neutral-100 hover:text-neutral-900 focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:outline-none"
    >
      <CircleUserRound className="size-6" />
    </Link>
  );
}

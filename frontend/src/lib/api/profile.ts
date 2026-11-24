import { apiFetch } from "./client";
import type { CatalogItem, Profile, ProfileUpdate, PublicProfile } from "@/types/profile";

export const getProfile = () => apiFetch<Profile>("/me");

/** Another user's public profile (name and skills). */
export const getUserProfile = (id: number) => apiFetch<PublicProfile>(`/users/${id}`);

export const saveProfile = (data: ProfileUpdate) =>
  apiFetch<Profile>("/me", { method: "PUT", body: data });

export const getSkillCatalog = () => apiFetch<CatalogItem[]>("/skills");

/** Interests are stored as "hobbies" in the backend. */
export const getInterestCatalog = () => apiFetch<CatalogItem[]>("/hobbies");

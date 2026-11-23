import { apiFetch } from "./client";
import type { CatalogItem, Profile, ProfileUpdate } from "@/types/profile";

export const getProfile = () => apiFetch<Profile>("/me");

export const saveProfile = (data: ProfileUpdate) =>
  apiFetch<Profile>("/me", { method: "PUT", body: data });

export const getSkillCatalog = () => apiFetch<CatalogItem[]>("/skills");

/** Interests are stored as "hobbies" in the backend. */
export const getInterestCatalog = () => apiFetch<CatalogItem[]>("/hobbies");

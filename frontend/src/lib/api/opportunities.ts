import { apiFetch } from "./client";
import type { FeedFilters, FeedItem, Opportunity, OpportunityCreate } from "@/types/opportunity";

export const createOpportunity = (data: OpportunityCreate) =>
  apiFetch<Opportunity>("/opportunities", { method: "POST", body: data });

/** Opportunities ordered by how well they fit the signed-in user's interests. */
export const getOpportunityFeed = (filters: FeedFilters = {}) =>
  apiFetch<FeedItem[]>("/opportunities/feed", { query: { ...filters } });

export const getOpportunity = (id: number) => apiFetch<Opportunity>(`/opportunities/${id}`);

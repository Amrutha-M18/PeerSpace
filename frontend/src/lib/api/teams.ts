import { apiFetch } from "./client";
import type { Opportunity } from "@/types/opportunity";
import type { Team, TeamCreate } from "@/types/teams";

export const getOpportunities = () => apiFetch<Opportunity[]>("/opportunities");

export const createTeam = (opportunityId: number, data: TeamCreate) =>
  apiFetch<Team>(`/opportunities/${opportunityId}/teams`, { method: "POST", body: data });

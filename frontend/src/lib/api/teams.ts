import { apiFetch } from "./client";
import type { JoinRequest } from "@/types/join-reqeust";
import type { Opportunity } from "@/types/opportunity";
import type { Team, TeamCreate } from "@/types/teams";

export const getOpportunities = () => apiFetch<Opportunity[]>("/opportunities");

export const createTeam = (opportunityId: number, data: TeamCreate) =>
  apiFetch<Team>(`/opportunities/${opportunityId}/teams`, { method: "POST", body: data });

/** All teams formed for one opportunity. */
export const getTeams = (opportunityId: number) => apiFetch<Team[]>(`/opportunities/${opportunityId}/teams`);

/** The signed-in user's join requests to teams of this opportunity (newest first). */
export const getMyRequests = (opportunityId: number) =>
  apiFetch<JoinRequest[]>(`/opportunities/${opportunityId}/my-requests`);

export const requestToJoin = (teamId: number, message?: string) =>
  apiFetch<JoinRequest>(`/teams/${teamId}/requests`, { method: "POST", body: { message: message || null } });

export const withdrawRequest = (teamId: number) =>
  apiFetch<void>(`/teams/${teamId}/requests/mine`, { method: "DELETE" });

/** Owner only: the team's pending requests, best match first. */
export const getRankedRequests = (teamId: number) =>
  apiFetch<{ request_id: number; user_id: number }[]>(`/teams/${teamId}/requests/ranked`);

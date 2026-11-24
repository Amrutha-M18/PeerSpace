import { apiFetch } from "./client";
import type { JoinRequest } from "@/types/join-reqeust";
import type { Opportunity } from "@/types/opportunity";
import type { Applicant, ApplicantOrder, Team, TeamCreate } from "@/types/teams";

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

export const getTeam = (teamId: number) => apiFetch<Team>(`/teams/${teamId}`);

/** Owner only: pending requests scored by the matching module. `focus` = skill IDs to weigh more. */
export function getApplicants(teamId: number, order: ApplicantOrder, focus: number[] = []) {
  const params = new URLSearchParams({ order });
  focus.forEach((id) => params.append("focus", String(id)));
  return apiFetch<Applicant[]>(`/teams/${teamId}/applicants?${params}`);
}

/** Owner only. Returns the updated team. */
export const acceptRequest = (teamId: number, requestId: number) =>
  apiFetch<Team>(`/teams/${teamId}/requests/${requestId}/accept`, { method: "POST" });

export const declineRequest = (teamId: number, requestId: number) =>
  apiFetch<JoinRequest>(`/teams/${teamId}/requests/${requestId}/decline`, { method: "POST" });

/** Owner only. Returns the updated team. */
export const removeMember = (teamId: number, memberId: number) =>
  apiFetch<Team>(`/teams/${teamId}/members/${memberId}`, { method: "DELETE" });

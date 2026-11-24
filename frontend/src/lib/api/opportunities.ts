import { apiFetch } from "./client";
import type { Opportunity, OpportunityCreate } from "@/types/opportunity";

export const createOpportunity = (data: OpportunityCreate) =>
  apiFetch<Opportunity>("/opportunities", { method: "POST", body: data });

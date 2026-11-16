
import { apiFetch } from "./client";
import type { OpportunityResponse } from "@/types/opportunity";

export async function fetchOpportunities(
  domain: string,
): Promise<OpportunityResponse> {
  return apiFetch<OpportunityResponse>("/opportunities", {
    query: { domain },
  });
}

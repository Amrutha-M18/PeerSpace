
import type { OpportunityResponse } from "@/types/opportunity";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

export async function fetchOpportunities(
  domain: string,
): Promise<OpportunityResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/opportunities?domain=${encodeURIComponent(domain)}`,
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ?? "The server could not find opportunities.",
    );
  }

  return data as OpportunityResponse;
}

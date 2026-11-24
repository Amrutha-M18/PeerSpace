export const OPPORTUNITY_CATEGORIES = ["hackathon", "course project", "study group", "trek", "sport", "other"] as const;
export type OpportunityCategory = (typeof OPPORTUNITY_CATEGORIES)[number];

/** GET /api/opportunities */
export interface Opportunity {
  id: number;
  title: string;
  category: string;
  organizer: string | null;
  description: string | null;
  starts_on: string | null; // "YYYY-MM-DD"
  ends_on: string | null;
  official_url: string | null;
  is_team_based: boolean;
  team_size: number | null; // max people per team, if limited
  created_by_id: number | null;
  created_at: string;
}

/** POST /api/opportunities */
export interface OpportunityCreate {
  title: string;
  category: OpportunityCategory;
  organizer: string | null;
  description: string | null;
  starts_on: string | null;
  ends_on: string | null;
  official_url: string | null;
  is_team_based: boolean;
  team_size: number | null;
}

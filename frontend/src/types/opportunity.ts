/** GET /api/opportunities */
export interface Opportunity {
  id: number;
  title: string;
  category: string;
  organizer: string | null;
  description: string | null;
  starts_on: string | null;
  ends_on: string | null;
  official_url: string | null;
  team_size: number | null;
  created_at: string;
}

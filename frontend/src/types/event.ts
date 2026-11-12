export interface Event {
  id: number;
  type: string;
  user_id: number | null;
  opportunity_id: number | null;
  team_id: number | null;
  created_at: string;
}
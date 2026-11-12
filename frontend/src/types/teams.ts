export interface Team {
  id: number;
  opportunity_id: number;
  owner_id: number;
  name: string;
  capacity: number;
  needed_skills: string[];
  status: string;
  created_at: string;
}
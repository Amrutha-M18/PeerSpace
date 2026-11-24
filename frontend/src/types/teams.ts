/** GET /api/teams/{id} and GET /api/opportunities/{id}/teams */
export interface TeamMember {
  id: number;
  name: string;
  /** Empty for people added by name who aren't on PeerSpace. */
  user_id: number | null;
  role: "owner" | "member";
}

/** Must be met. `count` = how many members the team needs with this skill. */
export interface HardRequirement {
  skill_id: number;
  name: string;
  min_level: number;
  count: number;
}

/** Nice to have. */
export interface SoftRequirement {
  skill_id: number;
  name: string;
  min_level: number;
}

export interface Team {
  id: number;
  opportunity_id: number;
  owner_id: number;
  name: string;
  description: string | null;
  /** Total team size, owner included. */
  capacity: number;
  status: "open" | "full";
  open_slots: number;
  members: TeamMember[];
  hard_requirements: HardRequirement[];
  soft_requirements: SoftRequirement[];
  created_at: string;
}

/** POST /api/opportunities/{id}/teams */
export interface TeamCreate {
  name: string;
  description?: string | null;
  capacity: number;
  default_members?: string[];
  hard_requirements?: { skill_id: number; min_level: number; count: number }[];
  soft_requirements?: { skill_id: number; min_level: number }[];
}

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
  /** Registered members already at min_level or above. */
  members_with_skill: number;
}

/** Nice to have. */
export interface SoftRequirement {
  skill_id: number;
  name: string;
  min_level: number;
  members_with_skill: number;
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

/** One of the team's skills compared with an applicant's level (from the matching module). */
export interface SkillCheck {
  skill_id: number;
  name: string;
  must_have: boolean;
  required_level: number;
  /** 0 = the applicant doesn't have it. */
  user_level: number;
  meets: boolean;
  /** A current member already meets it, so it counts for less in the score. */
  team_covers: boolean;
  in_focus: boolean;
}

/** GET /api/teams/{id}/applicants (owner only): a pending request with the applicant's details. */
export interface Applicant {
  request_id: number;
  user_id: number;
  name: string;
  message: string | null;
  requested_at: string;
  /** 0-100, from the matching module. */
  score: number;
  /** Meets every must-have. */
  eligible: boolean;
  missing_must_haves: string[];
  skill_checks: SkillCheck[];
  /** Skills the team didn't ask for, strongest first. */
  other_skills: { skill_id: number; name: string; level: number }[];
  interests: string[];
}

export type ApplicantOrder = "lowest_first" | "best_first";

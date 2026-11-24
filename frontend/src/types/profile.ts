/** One entry in the skill or interest catalogue (GET /api/skills, GET /api/hobbies). */
export interface CatalogItem {
  id: number;
  name: string;
}

export interface ProfileSkill {
  skill_id: number;
  name: string;
  level: number;
}

/** The backend calls interests "hobbies". Interests have no level. */
export interface ProfileHobby {
  hobby_id: number;
  name: string;
}

/** GET/PUT /api/me */
export interface Profile {
  id: number;
  email: string;
  name: string;
  skills: ProfileSkill[];
  hobbies: ProfileHobby[];
  created_at: string;
}

/** GET /api/users/{id}: what anyone signed in can see about a user. */
export interface PublicProfile {
  id: number;
  name: string;
  skills: ProfileSkill[];
}

export interface ProfileUpdate {
  name: string;
  skills: { skill_id: number; level: number }[];
  /** Hobby (interest) IDs. */
  hobbies: number[];
}

/** Selected tiles: catalogue id -> level, or null until the user picks a level (always null for interests). */
export type Selections = Record<number, number | null>;

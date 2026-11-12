
export type OpportunityType =
  | "Research project"
  | "Industry internship";

export type Opportunity = {
  title: string;
  organisation: string;
  domain: string;
  type: OpportunityType;
  description: string;
  apply_url: string;
  source_name: string;
  source_url: string;
};

export type OpportunityResponse = {
  domain: string;
  opportunities: Opportunity[];
  warnings: string[];
  fetched_at: string;
};

export type DomainOption = {
  value: string;
  label: string;
};

/*
export interface Opportunity {
  id: number;
  title: string;
  description: string | null;
  category: string;
  source: string;
  is_team_based: boolean;
  starts_on: string | null;
  ends_on: string | null;
  official_url: string | null;
  team_size: number | null;
  created_by_id: number | null;
  created_at: string;
}

export interface DomainOption {
  label: string;
  value: string;
}

export interface OpportunityResponse {
  opportunities: Opportunity[];
  total: number;
}
*/
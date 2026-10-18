
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

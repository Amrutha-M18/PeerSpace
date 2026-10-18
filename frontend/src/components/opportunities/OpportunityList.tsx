
import type { Opportunity } from "@/types/opportunity";

import OpportunityCard from "./OpportunityCard";

export default function OpportunityList({
  opportunities,
}: {
  opportunities: Opportunity[];
}) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {opportunities.map((opportunity, index) => (
        <OpportunityCard
          key={`${opportunity.apply_url}-${index}`}
          opportunity={opportunity}
        />
      ))}
    </div>
  );
}

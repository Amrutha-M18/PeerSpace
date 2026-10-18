
import type { Opportunity } from "@/types/opportunity";

import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card";

import { Badge } from "@/components/ui/badge";

export default function OpportunityCard({
  opportunity,
}: {
  opportunity: Opportunity;
}) {
  const isIndustryInternship =
    opportunity.type === "Industry internship";

  return (
    <Card className="flex h-full flex-col border-slate-200 bg-white shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md">
      <CardHeader className="gap-3 pb-3">
        <Badge
          variant="secondary"
          className={`w-fit ${
            isIndustryInternship
              ? "bg-orange-100 text-orange-800 hover:bg-orange-100"
              : "bg-emerald-100 text-emerald-800 hover:bg-emerald-100"
          }`}
        >
          {opportunity.type}
        </Badge>

        <h3 className="text-xl font-semibold leading-snug tracking-tight">
          {opportunity.title}
        </h3>

        <p className="text-sm font-semibold text-slate-600">
          {opportunity.organisation}
        </p>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col">
        <p className="flex-1 text-sm leading-relaxed text-slate-600">
          {opportunity.description}
        </p>

        <p className="mt-5 text-xs text-slate-500">
          Source: {opportunity.source_name}
        </p>

        <a
          href={opportunity.apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex w-fit items-center gap-2 font-semibold text-blue-600 transition-colors hover:text-blue-800 hover:underline"
        >
          {isIndustryInternship
            ? "View internship"
            : "View project"}

          <span aria-hidden="true">↗</span>
        </a>
      </CardContent>
    </Card>
  );
}

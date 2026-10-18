
import type {
  DomainOption,
  OpportunityResponse,
} from "@/types/opportunity";

import OpportunityList from "./OpportunityList";
import StatusMessage from "@/components/ui/StatusMessage";

type OpportunityResultsProps = {
  results: OpportunityResponse | null;
  isLoading: boolean;
  error: string;
  domains: DomainOption[];
};

export default function OpportunityResults({
  results,
  isLoading,
  error,
  domains,
}: OpportunityResultsProps) {
  const industryOpportunities =
    results?.opportunities.filter(
      (item) => item.type === "Industry internship",
    ) ?? [];

  const researchOpportunities =
    results?.opportunities.filter(
      (item) => item.type === "Research project",
    ) ?? [];

  const domainLabel =
    domains.find((item) => item.value === results?.domain)
      ?.label ?? results?.domain;

  return (
    <section
      className="space-y-8"
      aria-live="polite"
      aria-busy={isLoading}
    >
      {isLoading && (
        <StatusMessage variant="status">
          Checking public sources for current opportunities...
        </StatusMessage>
      )}

      {error && (
        <StatusMessage variant="error">
          {error} Make sure the FastAPI server is running,
          then try again.
        </StatusMessage>
      )}

      {results && (
        <>
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <p className="mb-2 text-xs font-bold tracking-[0.16em] text-blue-600">
                RESULTS
              </p>

              <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
                Opportunities for {domainLabel}
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                {results.opportunities.length} opportunities found
              </p>
            </div>

            <p className="text-sm text-slate-500">
              Fetched{" "}
              {new Date(
                results.fetched_at,
              ).toLocaleTimeString()}
            </p>
          </div>

          {results.warnings.length > 0 && (
            <StatusMessage variant="warning">
              Some sources were unavailable.{" "}
              {results.warnings.join(" ")}
            </StatusMessage>
          )}

          {results.opportunities.length === 0 ? (
            <StatusMessage variant="status">
              No readable listings were found. Try again later
              or open the source pages directly.
            </StatusMessage>
          ) : (
            <div className="space-y-10">
              {industryOpportunities.length > 0 && (
                <section className="space-y-4">
                  <h3 className="text-xl font-semibold tracking-tight">
                    Industry internships
                    <span className="ml-2 text-sm font-normal text-slate-500">
                      ({industryOpportunities.length})
                    </span>
                  </h3>

                  <OpportunityList
                    opportunities={industryOpportunities}
                  />
                </section>
              )}

              {researchOpportunities.length > 0 && (
                <section className="space-y-4">
                  <h3 className="text-xl font-semibold tracking-tight">
                    Research projects
                    <span className="ml-2 text-sm font-normal text-slate-500">
                      ({researchOpportunities.length})
                    </span>
                  </h3>

                  <OpportunityList
                    opportunities={researchOpportunities}
                  />
                </section>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}

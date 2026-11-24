import { notFound } from "next/navigation";
import { OpportunityTeamsView } from "@/components/opportunities/OpportunityTeamsView";

export const metadata = { title: "Opportunity · PeerSpace" };

/** /opportunities/3, plus ?created=team&team=7 right after creating something. */
export default async function OpportunityPage({ params, searchParams }: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ created?: string; team?: string }>;
}) {
  const [{ id }, { created, team }] = await Promise.all([params, searchParams]);
  const opportunityId = Number(id);
  if (!Number.isInteger(opportunityId) || opportunityId < 1) notFound();
  return (
    <OpportunityTeamsView
      key={id}
      opportunityId={opportunityId}
      created={created === "team" || created === "opportunity" ? created : undefined}
      highlightTeamId={team ? Number(team) : undefined}
    />
  );
}

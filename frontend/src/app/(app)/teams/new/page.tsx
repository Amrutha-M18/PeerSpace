import { CreateTeamForm } from "@/components/teams/CreateTeamForm";

export const metadata = { title: "Create a team · PeerSpace" };

/** /teams/new, or /teams/new?opportunity=3 to preselect an opportunity. */
export default async function NewTeamPage({ searchParams }: { searchParams: Promise<{ opportunity?: string }> }) {
  const { opportunity } = await searchParams;
  return <CreateTeamForm initialOpportunityId={opportunity} />;
}

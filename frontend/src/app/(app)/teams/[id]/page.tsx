import { notFound } from "next/navigation";
import { TeamDetailsView } from "@/components/teams/TeamDetailsView";

export const metadata = { title: "Team · PeerSpace" };

/** /teams/7: team details for everyone; join requests for the owner. */
export default async function TeamPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const teamId = Number(id);
  if (!Number.isInteger(teamId) || teamId < 1) notFound();
  return <TeamDetailsView key={id} teamId={teamId} />;
}

import { UserProfileView } from "@/components/profile/UserProfileView";

export const metadata = { title: "Profile · PeerSpace" };

export default async function UserProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <UserProfileView key={id} userId={id} />; // key: reset state when switching users
}

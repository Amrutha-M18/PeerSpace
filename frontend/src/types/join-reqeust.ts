export interface JoinRequest {
  id: number;
  team_id: number;
  user_id: number;
  message: string | null;
  status: "pending" | "accepted" | "rejected";
  created_at: string;
}
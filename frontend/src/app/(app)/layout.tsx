import { RequireAuth } from "@/components/auth/RequireAuth";

/** Every page in the (app) group requires login. Public pages (login, register) live in (public). */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}

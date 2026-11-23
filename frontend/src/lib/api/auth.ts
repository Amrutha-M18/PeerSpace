import { apiFetch } from "./client";
import type { User } from "@/types/user";

type AuthResponse = { access_token: string; token_type: string; user: User };

export const login = (email: string, password: string) =>
  apiFetch<AuthResponse>("/auth/login", { method: "POST", body: { email, password } });

export const register = (name: string, email: string, password: string) =>
  apiFetch<AuthResponse>("/auth/register", { method: "POST", body: { name, email, password } });

export const logout = () => apiFetch<void>("/auth/logout", { method: "POST" });

export const getMe = () => apiFetch<User>("/auth/me");
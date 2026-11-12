export interface User {
  id: number;
  email: string;
  name: string;
  department: string | null;
  year: string | null;
  skills: string[];
  availability: string[];
  created_at: string;
}
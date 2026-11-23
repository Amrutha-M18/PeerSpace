/** Proficiency levels shown in the UI, and the number saved in the database (1-5 is allowed there). */
export const PROFICIENCY_LEVELS = [
  { value: 1, label: "Beginner" },
  { value: 2, label: "Intermediate" },
  { value: 3, label: "Advanced" },
  { value: 4, label: "Expert" },
] as const;

/** Older data may hold level 5; show it as Expert. */
export function toUiLevel(level: number): number {
  return Math.min(Math.max(level, 1), 4);
}

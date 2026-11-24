/** Small display helpers shared by the opportunity pages. */

export const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

/** "2026-12-01" -> "1 Dec 2026" (read as a local date, so it never shifts a day). */
export function formatDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

/** A start/end pair as one readable line. */
export function dateRange(start: string | null, end: string | null) {
  if (start && end) return start === end ? formatDate(start) : `${formatDate(start)} – ${formatDate(end)}`;
  if (start) return `From ${formatDate(start)}`;
  if (end) return `Until ${formatDate(end)}`;
  return "Dates to be announced";
}

/** True once the last day (end, or start if there's no end) is before today. */
export function isOver(start: string | null, end: string | null) {
  const last = end ?? start;
  if (!last) return false;
  const today = new Date();
  const todayText = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  return last < todayText;
}

/** "just now", "5 min ago", "3 hours ago", "2 days ago", then a date. */
export function timeAgo(iso: string) {
  // The database stores UTC times without a zone ("2026-11-24T09:12:07"); read those as UTC.
  const time = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  const minutes = Math.max(0, Math.round((Date.now() - time.getTime()) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;
  const days = Math.round(hours / 24);
  if (days < 14) return `${days} ${days === 1 ? "day" : "days"} ago`;
  return time.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

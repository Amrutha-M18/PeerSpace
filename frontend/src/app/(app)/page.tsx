import { redirect } from "next/navigation";

/** The opportunity dashboard is the home page for signed-in users. */
export default function Home() {
  redirect("/opportunities");
}

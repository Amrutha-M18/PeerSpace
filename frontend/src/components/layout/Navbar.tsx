import Link from "next/link";
import { UserMenu } from "./UserMenu";

/** Top bar shown on every page: app name on the left, user icon on the right. */
export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-neutral-200 bg-white">
      <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-neutral-900">
          PeerSpace
        </Link>
        <UserMenu />
      </nav>
    </header>
  );
}

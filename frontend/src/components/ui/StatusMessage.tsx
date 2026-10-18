
import type { ReactNode } from "react";

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";

type StatusMessageProps = {
  variant: "status" | "error" | "warning";
  children: ReactNode;
};

export default function StatusMessage({
  variant,
  children,
}: StatusMessageProps) {
  if (variant === "status") {
    return (
      <div
        role="status"
        className="my-6 rounded-lg border bg-slate-50 px-4 py-4 text-sm leading-relaxed text-slate-600"
      >
        {children}
      </div>
    );
  }

  const isError = variant === "error";

  return (
    <Alert
      variant="default"
      className={
        isError
          ? "my-6 border-rose-200 bg-rose-50 text-rose-900 [&>svg]:text-rose-600"
          : "my-6 border-orange-200 bg-orange-50 text-orange-900 [&>svg]:text-orange-600"
      }
    >
      <AlertTitle>
        {isError ? "Search failed" : "Source warning"}
      </AlertTitle>

      <AlertDescription className="leading-relaxed">
        {children}
      </AlertDescription>
    </Alert>
  );
}

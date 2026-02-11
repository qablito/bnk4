"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CollapsibleProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  "data-testid"?: string;
}

export function Collapsible({
  title,
  children,
  defaultOpen = false,
  ...props
}: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div data-testid={props["data-testid"]}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        data-testid={props["data-testid"] ? `${props["data-testid"]}-trigger` : undefined}
        className="flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors w-full text-left py-2"
      >
        <svg
          className={cn(
            "w-4 h-4 transition-transform",
            open && "rotate-90"
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        {title}
      </button>
      {open && (
        <div
          data-testid={props["data-testid"] ? `${props["data-testid"]}-content` : undefined}
          className="pl-6 pb-2"
        >
          {children}
        </div>
      )}
    </div>
  );
}

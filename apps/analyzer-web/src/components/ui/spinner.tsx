import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  "data-testid"?: string;
}

export function Spinner({ className, ...props }: SpinnerProps) {
  return (
    <div
      data-testid={props["data-testid"] || "spinner"}
      role="status"
      className={cn("flex items-center justify-center", className)}
    >
      <svg
        className="animate-spin h-6 w-6 text-accent"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      <span className="sr-only">Loading...</span>
    </div>
  );
}

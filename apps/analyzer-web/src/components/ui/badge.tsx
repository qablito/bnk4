import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  "data-testid"?: string;
}

export function Badge({ children, className, ...props }: BadgeProps) {
  return (
    <span
      data-testid={props["data-testid"]}
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        className
      )}
    >
      {children}
    </span>
  );
}

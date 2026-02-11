import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  "data-testid"?: string;
}

export function Card({ children, className, ...props }: CardProps) {
  return (
    <div
      data-testid={props["data-testid"]}
      className={cn("glass rounded-2xl p-6", className)}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-center justify-between mb-4", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h3 className={cn("text-sm font-semibold uppercase tracking-wide text-text-secondary", className)}>
      {children}
    </h3>
  );
}

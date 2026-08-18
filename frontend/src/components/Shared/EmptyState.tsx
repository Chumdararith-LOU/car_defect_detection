import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  title: string;
  hint?: string;
  icon?: ReactNode;
  className?: string;
}

export function EmptyState({ title, hint, icon, className }: Props) {
  return (
    <div className={cn("rounded-md border border-dashed border-border p-8 text-center", className)}>
      {icon && (
        <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-md bg-muted/50 text-muted-foreground">
          {icon}
        </div>
      )}
      <p className="text-xs font-medium text-muted-foreground">{title}</p>
      {hint && <p className="mt-1 text-[10px] text-muted-foreground/70">{hint}</p>}
    </div>
  );
}

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export type BadgeTone = "green" | "red" | "blue" | "yellow" | "gray" | "purple" | "emerald";

const TONE_CLASSES: Record<BadgeTone, string> = {
  green: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
  red: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30",
  blue: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
  yellow: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-500/30",
  gray: "bg-gray-500/15 text-gray-700 dark:text-gray-400 border-gray-500/30",
  purple: "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30",
  emerald: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
};

interface Props {
  tone: BadgeTone;
  children: ReactNode;
  icon?: ReactNode;
  uppercase?: boolean;
  size?: "sm" | "md";
  className?: string;
}

export function StatusBadge({
  tone,
  children,
  icon,
  uppercase = false,
  size = "sm",
  className,
}: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border",
        size === "md"
          ? "px-2.5 py-0.5 text-xs font-medium"
          : "px-2 py-0.5 text-[10px] font-semibold",
        uppercase && "uppercase tracking-wider",
        TONE_CLASSES[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}

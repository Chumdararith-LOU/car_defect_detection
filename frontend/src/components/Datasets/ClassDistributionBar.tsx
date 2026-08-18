import type { ClassDistributionItem } from "@/lib/inspection/schema";

interface Props {
  distribution: ClassDistributionItem[];
}

// Explicit color array to avoid Tailwind v4 purge issues with dynamic classes
const COLORS = [
  "bg-blue-500", "bg-emerald-500", "bg-amber-500", "bg-rose-500",
  "bg-violet-500", "bg-cyan-500", "bg-pink-500", "bg-lime-500",
  "bg-orange-500", "bg-teal-500", "bg-indigo-500", "bg-yellow-500",
];

export function ClassDistributionBar({ distribution }: Props) {
  if (!distribution || distribution.length === 0) {
    return <p className="text-xs text-muted-foreground">No distribution data.</p>;
  }

  const nonZero = distribution.filter((d) => d.instance_count > 0);
  const totalInstances = nonZero.reduce((sum, d) => sum + d.instance_count, 0);

  if (totalInstances === 0) {
    return <p className="text-xs text-muted-foreground">No instances found in label files.</p>;
  }

  return (
    <div className="space-y-3">
      {/* Stacked Bar */}
      <div className="flex h-4 w-full overflow-hidden rounded-md border border-border bg-muted/30">
        {nonZero.map((item) => {
          const widthPct = (item.instance_count / totalInstances) * 100;
          const colorClass = COLORS[item.class_id % COLORS.length];
          return (
            <div
              key={item.class_id}
              className={`h-full ${colorClass} transition-all`}
              style={{ width: `${widthPct}%` }}
              title={`${item.class_name}: ${item.instance_count} (${item.percentage}%)`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-x-4 gap-y-1.5 text-xs">
        {distribution.map((item) => {
          const colorClass = COLORS[item.class_id % COLORS.length];
          return (
            <div key={item.class_id} className="flex items-center gap-1.5">
              <span className={`inline-block h-2.5 w-2.5 rounded-sm ${colorClass}`} />
              <span className="font-medium text-foreground truncate">{item.class_name}</span>
              <span className="text-muted-foreground">
                {item.instance_count} ({item.percentage}%)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

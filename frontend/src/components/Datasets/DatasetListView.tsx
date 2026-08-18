import type { DatasetSummary } from "@/lib/inspection/schema";
import { getStageBadgeTone, getStatusBadgeTone } from "./datasetUtils";
import { EmptyState, StatusBadge } from "@/components/Shared";
import { Award, ChevronRight } from "lucide-react";

interface Props {
  datasets: DatasetSummary[];
  onSelect: (datasetId: string) => void;
}

export function DatasetListView({ datasets, onSelect }: Props) {
  if (datasets.length === 0) {
    return <EmptyState title="No datasets found" hint="Nothing in data/processed/ yet." />;
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b border-border">
          <tr className="text-left text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
            <th className="px-4 py-2.5">Name</th>
            <th className="px-4 py-2.5">Stage</th>
            <th className="px-4 py-2.5 text-right">Images</th>
            <th className="px-4 py-2.5 text-right">Classes</th>
            <th className="px-4 py-2.5">Status</th>
            <th className="px-4 py-2.5 w-10"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {datasets.map((ds) => (
            <tr
              key={ds.dataset_id}
              onClick={() => onSelect(ds.dataset_id)}
              className="hover:bg-muted/30 cursor-pointer transition-colors"
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{ds.name}</span>
                  {ds.is_champion && <Award className="h-3.5 w-3.5 text-yellow-500" />}
                </div>
              </td>
              <td className="px-4 py-3">
                <StatusBadge tone={getStageBadgeTone(ds.stage)} uppercase>
                  {ds.stage}
                </StatusBadge>
              </td>
              <td className="px-4 py-3 text-right font-mono">{ds.total_images.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-mono">{ds.nc}</td>
              <td className="px-4 py-3">
                <StatusBadge tone={getStatusBadgeTone(ds.status)} className="capitalize">
                  {ds.status}
                </StatusBadge>
              </td>
              <td className="px-4 py-3 text-right">
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

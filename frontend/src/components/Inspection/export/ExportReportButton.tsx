import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import type { InspectionPayload } from "@/lib/inspection/schema";
import { buildReportJson, buildReportFilename } from "./reportBuilder";

interface Props {
  payload: InspectionPayload | null;
}

export function ExportReportButton({ payload }: Props) {
  const [includePolygons, setIncludePolygons] = useState(false);

  const disabled = !payload;

  const handleExport = () => {
    if (!payload) return;
    const json = buildReportJson(payload, {
      includePanelPolygons: includePolygons,
    });
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = buildReportFilename(payload.inspection_id);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex items-center gap-3">
      <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none">
        <input
          type="checkbox"
          checked={includePolygons}
          onChange={(e) => setIncludePolygons(e.target.checked)}
          className="rounded border-gray-300"
        />
        Include panel polygons
      </label>
      <Button
        variant="outline"
        size="sm"
        onClick={handleExport}
        disabled={disabled}
        title={disabled ? "Run an inspection first" : "Download factory report"}
      >
        <Download className="h-4 w-4 mr-1.5" />
        Export Report
      </Button>
    </div>
  );
}

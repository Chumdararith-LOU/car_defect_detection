import type { InspectionPayload } from "@/lib/inspection/schema";

export interface ReportOptions {
  includePanelPolygons: boolean;
}

export function buildReportJson(payload: InspectionPayload, options: ReportOptions): string {
  const defects = payload.defects || [];
  const anomalies = payload.unclassified_anomalies || [];
  const suppressed = payload.suppressed_detections || [];
  const panels = payload.panels || [];

  // Severity summary
  const dsiValues = defects.map((d) => d.dsi).filter((v): v is number => v != null && v > 0);
  const maxDsi = dsiValues.length > 0 ? Math.max(...dsiValues) : 0;
  const avgDsi =
    dsiValues.length > 0 ? dsiValues.reduce((sum, v) => sum + v, 0) / dsiValues.length : 0;

  // Defect count by class
  const countByClass: Record<string, number> = {};
  for (const d of defects) {
    countByClass[d.class] = (countByClass[d.class] || 0) + 1;
  }

  // Panels — optionally include polygons
  const panelsReport = options.includePanelPolygons
    ? panels.map((p) => ({
        id: p.id,
        label: p.label,
        polygon: p.polygon,
        activeArea: p.activeArea,
      }))
    : panels.map((p) => ({
        id: p.id,
        label: p.label,
        activeArea: p.activeArea,
      }));

  const report = {
    report_version: "0.1",
    generated_at: new Date().toISOString(),
    inspection_id: payload.inspection_id,
    timestamp: payload.timestamp,
    verdict: payload.inspection_status,
    vehicle_color_detected: payload.vehicle_color_detected,
    total_defects_found: payload.total_defects_found,
    severity_summary: {
      max_dsi: Math.round(maxDsi * 100) / 100,
      avg_dsi: Math.round(avgDsi * 100) / 100,
      defect_count_by_class: countByClass,
    },
    panels_detected: panels.length,
    panels: panelsReport,
    defects: defects.map((d) => ({
      id: d.id,
      class: d.class,
      confidence: d.confidence,
      panel: d.panel,
      iod: d.iod,
      dsi: d.dsi,
      bbox: d.bbox,
      polygon: d.polygon,
    })),
    unclassified_anomalies: anomalies.map((a) => ({
      id: a.id,
      confidence: a.confidence,
      panel: a.panel,
      reason: a.reason,
      bbox: a.bbox,
    })),
    suppressed_detections: suppressed.map((s) => ({
      id: s.id,
      predicted_class: s.predicted_class,
      confidence: s.confidence,
      panel: s.panel,
      reason: s.reason,
      bbox: s.bbox,
    })),
  };

  return JSON.stringify(report, null, 2);
}

export function buildReportFilename(inspectionId: string): string {
  const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  return `inspection_${inspectionId}_${ts}.json`;
}

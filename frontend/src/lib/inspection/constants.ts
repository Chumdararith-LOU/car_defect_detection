import type { DefectClass, PanelId } from "@/lib/inspection/schema";

export const DEFECT_CLASSES: { id: DefectClass; label: string; color: string }[] = [
  { id: "anomaly", label: "Anomaly (SOD)", color: "var(--defect-anomaly)" },
  { id: "dent", label: "Dent", color: "var(--defect-dent)" },
  { id: "scratch", label: "Scratch", color: "var(--defect-scratch)" },
  { id: "crack", label: "Crack", color: "var(--defect-crack)" },
  { id: "glass_shatter", label: "Glass Shatter", color: "var(--defect-glass_shatter)" },
  { id: "broken_lamp", label: "Broken Lamp", color: "var(--defect-broken_lamp)" },
  { id: "corrosion", label: "Corrosion", color: "var(--defect-corrosion)" },
  { id: "disjoint_part", label: "Disjoint Part", color: "var(--defect-disjoint_part)" },
];

export const PANEL_LABELS: Record<PanelId, string> = {
  quarter_panel: "Quarter Panel",
  front_wheel: "Front Wheel",
  back_window: "Back Window",
  trunk: "Trunk",
  front_door: "Front Door",
  rocker_panel: "Rocker Panel",
  grille: "Grille",
  windshield: "Windshield",
  front_window: "Front Window",
  back_door: "Back Door",
  headlight: "Headlight",
  back_wheel: "Back Wheel",
  back_windshield: "Back Windshield",
  hood: "Hood",
  fender: "Fender",
  tail_light: "Tail Light",
  license_plate: "License Plate",
  front_bumper: "Front Bumper",
  back_bumper: "Back Bumper",
  mirror: "Mirror",
  roof: "Roof",
  Unknown: "Unmapped",
};
export const ALL_PANELS = (Object.keys(PANEL_LABELS) as PanelId[]).filter(
  (p) => p !== "Unknown",
);

export function classColor(cls: DefectClass): string {
  return `var(--defect-${cls})`;
}

export function panelColor(label: string): string {
  const id = label.toLowerCase().replace(/-/g, "_");
  const idx = ALL_PANELS.indexOf(id as any);
  const hue = idx >= 0 ? (idx * 137.508) % 360 : 0;
  const light = idx % 2 === 0 ? 55 : 65;
  return `hsl(${Math.round(hue)} 70% ${light}%)`;
}

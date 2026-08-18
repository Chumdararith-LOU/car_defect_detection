import type { DatasetImageAnnotation } from "@/lib/inspection/schema";

interface Props {
  annotations: DatasetImageAnnotation[];
  width: number;
  height: number;
  visible: boolean;
}

const COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
  "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16",
];

export function MaskOverlay({ annotations, width, height, visible }: Props) {
  if (!visible || annotations.length === 0 || width === 0 || height === 0) return null;

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
    >
      {annotations.map((ann) => {
        const color = COLORS[ann.class_id % COLORS.length];
        const points = ann.polygon.map(([x, y]) => `${x * width},${y * height}`).join(" ");
        return (
          <g key={ann.index}>
            <polygon
              points={points}
              fill={color}
              fillOpacity={0.3}
              stroke={color}
              strokeWidth={2}
            />
            {ann.polygon.length > 0 && (
              <text
                x={ann.polygon[0][0] * width}
                y={ann.polygon[0][1] * height - 4}
                fill="white"
                fontSize="14"
                fontWeight="bold"
                style={{ textShadow: "1px 1px 2px black" }}
              >
                {ann.class_name}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { listRecipePresets } from "@/lib/inspection/apiClient";
import type { Recipe } from "@/lib/inspection/platformSchema";

interface Props {
  onSelect: (preset: Recipe) => void;
}

export function StrategyPresetPicker({ onSelect }: Props) {
  const [presets, setPresets] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listRecipePresets()
      .then((res) => setPresets(res.recipes))
      .catch(() => setPresets([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading presets...</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {presets.map((preset) => (
        <Card
          key={preset.id}
          className="cursor-pointer transition hover:border-primary"
          onClick={() => onSelect(preset)}
        >
          <CardHeader>
            <CardTitle className="text-sm">{preset.name}</CardTitle>
          </CardHeader>
          <CardContent>
            {preset.description && (
              <p className="mb-3 text-xs text-muted-foreground">{preset.description}</p>
            )}
            <dl className="space-y-1 text-xs">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Freeze:</dt>
                <dd className="font-mono">{preset.freeze_mode}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">LR mode:</dt>
                <dd className="font-mono">{preset.lr_mode}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Loss:</dt>
                <dd className="font-mono">{preset.loss_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Epochs:</dt>
                <dd className="font-mono">{preset.epochs}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">imgsz:</dt>
                <dd className="font-mono">{preset.imgsz}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

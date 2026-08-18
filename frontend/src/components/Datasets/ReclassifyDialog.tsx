import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface Props {
  classNames: string[];
  currentClassId: number;
  onConfirm: (newClassId: number) => Promise<void>;
  onCancel: () => void;
}

export function ReclassifyDialog({ classNames, currentClassId, onConfirm, onCancel }: Props) {
  const [selectedClass, setSelectedClass] = useState(currentClassId);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setSaving(true);
    setError(null);
    try {
      await onConfirm(selectedClass);
    } catch (err: any) {
      setError(err.message || "Failed to reclassify");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50" onClick={onCancel}>
      <div
        className="w-80 rounded-lg border border-border bg-card p-5 shadow-xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h4 className="text-sm font-semibold">Reclassify Annotation</h4>

        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Current class</label>
          <p className="text-sm font-mono font-medium">
            {classNames[currentClassId] || `class_${currentClassId}`}
          </p>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">New class</label>
          <select
            value={selectedClass}
            onChange={(e) => setSelectedClass(Number(e.target.value))}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {classNames.map((name, idx) => (
              <option key={idx} value={idx}>
                {name}
              </option>
            ))}
          </select>
        </div>

        {error && <p className="text-xs text-destructive">{error}</p>}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={saving || selectedClass === currentClassId}>
            {saving ? (
              <>
                <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                Saving...
              </>
            ) : (
              "Reclassify"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

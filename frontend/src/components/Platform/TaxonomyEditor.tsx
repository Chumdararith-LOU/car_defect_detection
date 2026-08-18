import { useEffect, useState } from "react";
import { ArrowUp, ArrowDown, X, Plus, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createTaxonomy, updateTaxonomy } from "@/lib/inspection/apiClient";
import type { Taxonomy, PlatformStage } from "@/lib/inspection/platformSchema";

interface Props {
  open: boolean;
  taxonomy: Taxonomy | null;
  onClose: () => void;
  onSaved: () => void;
}

export function TaxonomyEditor({ open, taxonomy, onClose, onSaved }: Props) {
  const isEdit = !!taxonomy;
  const [name, setName] = useState("");
  const [stage, setStage] = useState<PlatformStage>("stage2");
  const [classes, setClasses] = useState<string[]>([""]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      if (taxonomy) {
        setName(taxonomy.name);
        setStage(taxonomy.stage);
        setClasses(taxonomy.class_names.length > 0 ? [...taxonomy.class_names] : [""]);
      } else {
        setName("");
        setStage("stage2");
        setClasses([""]);
      }
      setError(null);
      setSaving(false);
    }
  }, [open, taxonomy]);

  const updateClass = (index: number, value: string) => {
    setClasses((prev) => prev.map((c, i) => (i === index ? value : c)));
  };

  const removeClass = (index: number) => {
    setClasses((prev) => prev.filter((_, i) => i !== index));
  };

  const moveClass = (index: number, direction: -1 | 1) => {
    setClasses((prev) => {
      const next = [...prev];
      const target = index + direction;
      if (target < 0 || target >= next.length) return prev;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const addClass = () => {
    setClasses((prev) => [...prev, ""]);
  };

  const validClasses = classes.map((c) => c.trim()).filter(Boolean);

  const handleSave = async () => {
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }
    if (validClasses.length === 0) {
      setError("At least one class name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (isEdit && taxonomy) {
        await updateTaxonomy(taxonomy.id, {
          name: name.trim(),
          class_names: validClasses,
        });
      } else {
        await createTaxonomy({
          name: name.trim(),
          stage,
          class_names: validClasses,
        });
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
    >
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Taxonomy" : "New Taxonomy"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="tax-name">Name</Label>
            <Input
              id="tax-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. big-defects"
            />
          </div>

          <div className="space-y-1.5">
            <Label>Stage</Label>
            <Select
              value={stage}
              onValueChange={(v) => setStage(v as PlatformStage)}
              disabled={isEdit}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="stage1">stage1</SelectItem>
                <SelectItem value="stage2">stage2</SelectItem>
                <SelectItem value="stage3">stage3</SelectItem>
              </SelectContent>
            </Select>
            {isEdit && (
              <p className="text-xs text-muted-foreground">
                Stage cannot be changed after creation.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>Classes</Label>
            <div className="space-y-2">
              {classes.map((cls, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <Input
                    value={cls}
                    onChange={(e) => updateClass(i, e.target.value)}
                    placeholder={`class_${i + 1}`}
                    className="flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => moveClass(i, -1)}
                    disabled={i === 0}
                    title="Move up"
                  >
                    <ArrowUp className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => moveClass(i, 1)}
                    disabled={i === classes.length - 1}
                    title="Move down"
                  >
                    <ArrowDown className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeClass(i)}
                    disabled={classes.length <= 1}
                    title="Remove"
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
            <Button variant="outline" size="sm" onClick={addClass}>
              <Plus className="mr-1 h-3.5 w-3.5" />
              Add class
            </Button>
          </div>

          <div className="rounded-md border border-border bg-muted/30 p-3">
            <p className="text-xs font-medium text-muted-foreground mb-1.5">
              Preview: {validClasses.length} class{validClasses.length !== 1 ? "es" : ""}
            </p>
            <div className="flex flex-wrap gap-1">
              {validClasses.map((c, i) => (
                <span
                  key={i}
                  className="inline-block rounded-sm bg-secondary px-1.5 py-0.5 text-[10px] font-mono text-secondary-foreground"
                >
                  {c}
                </span>
              ))}
              {validClasses.length === 0 && (
                <span className="text-[10px] text-muted-foreground">No classes yet</span>
              )}
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : isEdit ? (
              "Save Changes"
            ) : (
              "Create"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

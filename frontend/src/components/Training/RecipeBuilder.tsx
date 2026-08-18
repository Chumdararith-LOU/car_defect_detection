import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { CheckpointPicker, TaxonomyPicker } from "@/components/Platform";
import { createRecipe } from "@/lib/inspection/apiClient";
import type {
  BaseStrategy,
  FreezeMode,
  LossType,
  LrMode,
  Recipe,
  RecipeCreateRequest,
} from "@/lib/inspection/platformSchema";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  preset?: Recipe;
  onSaved?: () => void;
}

export function RecipeBuilder({ open, onOpenChange, preset, onSaved }: Props) {
  const [name, setName] = useState(preset?.name ?? "");
  const [description, setDescription] = useState(preset?.description ?? "");
  const [taxonomyId, setTaxonomyId] = useState<string | null>(preset?.taxonomy_id ?? null);
  const [baseStrategy, setBaseStrategy] = useState<BaseStrategy>(
    preset?.base_strategy ?? "from_checkpoint",
  );
  const [baseCheckpointId, setBaseCheckpointId] = useState<string | null>(
    preset?.base_checkpoint_id ?? null,
  );
  const [freezeMode, setFreezeMode] = useState<FreezeMode>(preset?.freeze_mode ?? "none");
  const [freezeLayers, setFreezeLayers] = useState(preset?.freeze_layers ?? null);
  const [lrMode, setLrMode] = useState<LrMode>(preset?.lr_mode ?? "uniform");
  const [splitLayerIdx, setSplitLayerIdx] = useState(preset?.split_layer_idx ?? null);
  const [backboneLrMult, setBackboneLrMult] = useState(preset?.backbone_lr_mult ?? null);
  const [lossType, setLossType] = useState<LossType>(preset?.loss_type ?? "bce");
  const [flGamma, setFlGamma] = useState(preset?.fl_gamma ?? 2.0);
  const [flAlpha, setFlAlpha] = useState(preset?.fl_alpha ?? 0.5);
  const [flScale, setFlScale] = useState(preset?.fl_scale ?? 1.0);
  const [imgsz, setImgsz] = useState(preset?.imgsz ?? 640);
  const [batchSize, setBatchSize] = useState(preset?.batch_size ?? 8);
  const [epochs, setEpochs] = useState(preset?.epochs ?? 100);
  const [optimizer, setOptimizer] = useState(preset?.optimizer ?? "SGD");
  const [lr0, setLr0] = useState(preset?.lr0 ?? 0.01);
  const [lrf, setLrf] = useState(preset?.lrf ?? 0.01);
  const [patience, setPatience] = useState(preset?.patience ?? 20);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    if (!name.trim() || !taxonomyId) {
      toast.error("Name and taxonomy are required");
      return;
    }
    setSaving(true);
    try {
      const req: RecipeCreateRequest = {
        name: name.trim(),
        taxonomy_id: taxonomyId,
        description: description.trim() || null,
        base_strategy: baseStrategy,
        base_checkpoint_id: baseCheckpointId,
        freeze_mode: freezeMode,
        freeze_layers: freezeMode !== "none" ? freezeLayers : null,
        lr_mode: lrMode,
        split_layer_idx: lrMode === "differential" ? splitLayerIdx : null,
        backbone_lr_mult: lrMode === "differential" ? backboneLrMult : null,
        loss_type: lossType,
        fl_gamma: flGamma,
        fl_alpha: flAlpha,
        fl_scale: flScale,
        imgsz,
        batch_size: batchSize,
        epochs,
        optimizer,
        lr0,
        lrf,
        patience,
        augmentations: null,
      };
      await createRecipe(req);
      toast.success("Recipe created");
      onSaved?.();
      onOpenChange(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to create recipe");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New Recipe</DialogTitle>
          <DialogDescription>
            Define a training strategy bound to a taxonomy.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Taxonomy</Label>
              <TaxonomyPicker value={taxonomyId} onChange={setTaxonomyId} />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Description</Label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Base strategy</Label>
              <Select value={baseStrategy} onValueChange={(v) => setBaseStrategy(v as BaseStrategy)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="native_coco">Native COCO</SelectItem>
                  <SelectItem value="from_checkpoint">From checkpoint</SelectItem>
                  <SelectItem value="from_previous_step">From previous step</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Base checkpoint</Label>
              <CheckpointPicker value={baseCheckpointId} onChange={setBaseCheckpointId} />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Freeze mode</Label>
              <Select value={freezeMode} onValueChange={(v) => setFreezeMode(v as FreezeMode)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="freeze_n">Freeze N layers</SelectItem>
                  <SelectItem value="head_only">Head only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {freezeMode !== "none" && (
              <div className="space-y-2">
                <Label>Freeze layers</Label>
                <Input
                  type="number"
                  value={freezeLayers ?? ""}
                  onChange={(e) => setFreezeLayers(e.target.value ? Number(e.target.value) : null)}
                />
              </div>
            )}
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>LR mode</Label>
              <Select value={lrMode} onValueChange={(v) => setLrMode(v as LrMode)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="uniform">Uniform</SelectItem>
                  <SelectItem value="differential">Differential</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {lrMode === "differential" && (
              <>
                <div className="space-y-2">
                  <Label>Split layer idx</Label>
                  <Input
                    type="number"
                    value={splitLayerIdx ?? ""}
                    onChange={(e) => setSplitLayerIdx(e.target.value ? Number(e.target.value) : null)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Backbone LR mult</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={backboneLrMult ?? ""}
                    onChange={(e) =>
                      setBackboneLrMult(e.target.value ? Number(e.target.value) : null)
                    }
                  />
                </div>
              </>
            )}
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Loss type</Label>
              <Select value={lossType} onValueChange={(v) => setLossType(v as LossType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bce">BCE</SelectItem>
                  <SelectItem value="focal">Focal</SelectItem>
                  <SelectItem value="ce">CE</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {lossType === "focal" && (
              <>
                <div className="space-y-2">
                  <Label>γ (gamma)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={flGamma}
                    onChange={(e) => setFlGamma(Number(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>α (alpha)</Label>
                  <Input
                    type="number"
                    step="0.05"
                    value={flAlpha}
                    onChange={(e) => setFlAlpha(Number(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Scale</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={flScale}
                    onChange={(e) => setFlScale(Number(e.target.value))}
                  />
                </div>
              </>
            )}
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>imgsz</Label>
              <Input
                type="number"
                value={imgsz}
                onChange={(e) => setImgsz(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>Batch size</Label>
              <Input
                type="number"
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>Epochs</Label>
              <Input
                type="number"
                value={epochs}
                onChange={(e) => setEpochs(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>Optimizer</Label>
              <Input value={optimizer} onChange={(e) => setOptimizer(e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>lr0</Label>
              <Input
                type="number"
                step="0.0001"
                value={lr0}
                onChange={(e) => setLr0(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>lrf</Label>
              <Input
                type="number"
                step="0.001"
                value={lrf}
                onChange={(e) => setLrf(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>Patience</Label>
              <Input
                type="number"
                value={patience}
                onChange={(e) => setPatience(Number(e.target.value))}
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Create Recipe"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

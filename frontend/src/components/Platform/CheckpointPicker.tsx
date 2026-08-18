import { useEffect, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listCheckpoints } from "@/lib/inspection/apiClient";
import type { Checkpoint } from "@/lib/inspection/platformSchema";

const NONE_VALUE = "__none__";

interface Props {
  stage?: string;
  value?: string | null;
  onChange: (id: string | null) => void;
}

export function CheckpointPicker({ stage, value, onChange }: Props) {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listCheckpoints(stage)
      .then((res) => {
        if (!cancelled) setCheckpoints(res.checkpoints);
      })
      .catch(() => {
        if (!cancelled) setCheckpoints([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [stage]);

  return (
    <Select
      value={value ?? NONE_VALUE}
      onValueChange={(v) => onChange(v === NONE_VALUE ? null : v)}
    >
      <SelectTrigger>
        <SelectValue placeholder={loading ? "Loading checkpoints..." : "Select a checkpoint"} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE_VALUE}>No checkpoint</SelectItem>
        {checkpoints.map((c) => (
          <SelectItem key={c.id} value={c.id}>
            {c.name} · {c.origin} · nc={c.nc}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

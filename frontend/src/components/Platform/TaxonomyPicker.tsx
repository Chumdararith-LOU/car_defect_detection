import { useEffect, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listTaxonomies } from "@/lib/inspection/apiClient";
import type { Taxonomy } from "@/lib/inspection/platformSchema";

const NONE_VALUE = "none";

interface Props {
  stage?: string;
  value?: string | null;
  onChange: (id: string | null) => void;
}

export function TaxonomyPicker({ stage, value, onChange }: Props) {
  const [taxonomies, setTaxonomies] = useState<Taxonomy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listTaxonomies(stage)
      .then((res) => {
        if (!cancelled) setTaxonomies(res.taxonomies);
      })
      .catch(() => {
        if (!cancelled) setTaxonomies([]);
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
        <SelectValue placeholder={loading ? "Loading taxonomies..." : "Select a taxonomy"} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE_VALUE}>No taxonomy</SelectItem>
        {taxonomies.map((t) => (
          <SelectItem key={t.id} value={t.id}>
            {t.name} · {t.stage} · {t.class_names.length} classes
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

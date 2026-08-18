/** Shared crop math for card previews (normalized bbox -> CSS background). */
export function cropBox(bbox: [number, number, number, number]) {
  const [x1, y1, x2, y2] = bbox;
  const w = Math.max(0, x2 - x1);
  const h = Math.max(0, y2 - y1);
  const pad = 0.02;
  const cx = Math.max(0, x1 - pad);
  const cy = Math.max(0, y1 - pad);
  const cw = Math.min(1 - cx, w + pad * 2);
  const ch = Math.min(1 - cy, h + pad * 2);
  return { x: x1, y: y1, w, h, cx, cy, cw, ch };
}

export function getCropStyle(
  imageUrl: string,
  bbox: [number, number, number, number],
) {
  const { cx, cy, cw, ch } = cropBox(bbox);
  return {
    backgroundImage: `url(${imageUrl})`,
    backgroundRepeat: "no-repeat",
    backgroundSize: `${100 / cw}% ${100 / ch}%`,
    backgroundPosition: `${(cx / (1 - cw)) * 100}% ${(cy / (1 - ch)) * 100}%`,
  } as const;
}

import type { FinalResultSummary } from "./consultationApi";

export function selectedPhotosLabel(result: FinalResultSummary): string {
  if (result.declaration === "none") return "No choice";
  return result.selected_ordinals
    .map((ordinal) => `Photo ${ordinal + 1}`)
    .join(", ");
}

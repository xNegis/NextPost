import { describe, expect, it } from "vitest";

import type { FinalResultSummary } from "./consultationApi";
import { selectedPhotosLabel } from "./finalizedResult";

const base: FinalResultSummary = {
  finalized_at: "2026-09-28T12:05:00Z",
  total_votes: 3,
  declaration: "selected",
  selected_ordinals: [0, 2],
  options: [
    { ordinal: 0, vote_count: 2, selected: true },
    { ordinal: 1, vote_count: 0, selected: false },
    { ordinal: 2, vote_count: 1, selected: true },
  ],
};

describe("selectedPhotosLabel", () => {
  it("renders a single selected photo", () => {
    expect(selectedPhotosLabel({ ...base, selected_ordinals: [0] })).toBe(
      "Photo 1",
    );
  });

  it("renders multiple selected photos in ordinal order", () => {
    expect(selectedPhotosLabel(base)).toBe("Photo 1, Photo 3");
  });

  it("renders no choice", () => {
    expect(
      selectedPhotosLabel({
        ...base,
        declaration: "none",
        selected_ordinals: [],
      }),
    ).toBe("No choice");
  });
});

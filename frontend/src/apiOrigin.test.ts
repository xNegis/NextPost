import { describe, expect, it } from "vitest";

import { normalizeApiBaseUrl } from "./apiOrigin";

describe("normalizeApiBaseUrl", () => {
  it("keeps browser requests same-origin", () => {
    expect(normalizeApiBaseUrl("", false)).toBe("");
  });

  it("accepts only the canonical mobile production origin", () => {
    expect(
      normalizeApiBaseUrl("https://nextpost.formcadence.app/", false),
    ).toBe("https://nextpost.formcadence.app");
    expect(() => normalizeApiBaseUrl("https://example.com", false)).toThrow(
      "approved origin",
    );
  });

  it("allows local HTTP origins only during development", () => {
    expect(normalizeApiBaseUrl("http://localhost:8000", true)).toBe(
      "http://localhost:8000",
    );
    expect(() => normalizeApiBaseUrl("http://localhost:8000", false)).toThrow(
      "approved origin",
    );
  });
});

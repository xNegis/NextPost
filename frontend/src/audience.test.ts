import { describe, expect, it } from "vitest";

import {
  AUDIENCE_INVALID_MESSAGE,
  AUDIENCE_MISSING_MESSAGE,
  PRIVATE,
  PUBLIC,
  isAudience,
  validateAudience,
} from "./audience";

describe("audience", () => {
  it("accepts the canonical public and private values", () => {
    expect(validateAudience(PUBLIC)).toBe(PUBLIC);
    expect(validateAudience(PRIVATE)).toBe(PRIVATE);
    expect(isAudience(PUBLIC)).toBe(true);
    expect(isAudience(PRIVATE)).toBe(true);
  });

  it.each([
    ["missing", null],
    ["case variant", "Public"],
    ["uppercase", "PRIVATE"],
    ["unknown", "unknown"],
    ["empty", ""],
    ["boolean", true],
    ["number", 1],
    ["array", ["public"]],
    ["object", { audience: "public" }],
  ])("rejects %s", (_label, value) => {
    expect(validateAudience(value)).toBeNull();
    expect(isAudience(value)).toBe(false);
  });

  it("distinguishes the missing message from the invalid message", () => {
    expect(AUDIENCE_MISSING_MESSAGE).toBe("Choose an audience.");
    expect(AUDIENCE_INVALID_MESSAGE).toBe("Choose Public or Private.");
  });
});

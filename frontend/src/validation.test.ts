import { describe, expect, it } from "vitest";

import { validateAlias, validateEmail, validatePassword } from "./validation";

describe("validateEmail", () => {
  it("accepts a valid email", () => {
    expect(validateEmail("ana@example.com")).toBeNull();
    expect(validateEmail("  ana@example.com  ")).toBeNull();
  });

  it("rejects empty and malformed emails", () => {
    expect(validateEmail("")).not.toBeNull();
    expect(validateEmail("   ")).not.toBeNull();
    expect(validateEmail("not-an-email")).not.toBeNull();
    expect(validateEmail("a@b")).not.toBeNull();
  });
});

describe("validateAlias", () => {
  it("accepts a valid alias", () => {
    expect(validateAlias("Ana")).toBeNull();
    expect(validateAlias("ana_1.2")).toBeNull();
  });

  it("rejects short, invalid-character, and no-alnum aliases", () => {
    expect(validateAlias("ab")).not.toBeNull();
    expect(validateAlias("has space")).not.toBeNull();
    expect(validateAlias("...")).not.toBeNull();
  });

  it("rejects reserved aliases case-insensitively", () => {
    expect(validateAlias("admin")).not.toBeNull();
    expect(validateAlias("Support")).not.toBeNull();
    expect(validateAlias("NEXTPOST")).not.toBeNull();
  });
});

describe("validatePassword", () => {
  it("accepts passwords within the length bounds", () => {
    expect(validatePassword("a".repeat(15))).toBeNull();
    expect(validatePassword("a".repeat(128))).toBeNull();
  });

  it("rejects too-short and too-long passwords", () => {
    expect(validatePassword("a".repeat(14))).not.toBeNull();
    expect(validatePassword("a".repeat(129))).not.toBeNull();
  });
});

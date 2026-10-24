import { describe, expect, it } from "vitest";

import { classifyLocation } from "./consultationRoute";

const UUID = "123e4567-e89b-12d3-a456-426614174000";
const TOKEN = `v1.${"A".repeat(43)}`;

describe("classifyLocation", () => {
  it("classifies the application root as root", () => {
    expect(
      classifyLocation("http://app.example/", "http://app.example"),
    ).toEqual({
      kind: "root",
    });
  });

  it("classifies the public privacy notice", () => {
    expect(classifyLocation("/privacy", "http://app.example")).toEqual({
      kind: "privacy",
    });
  });

  it("classifies a relative public consultation path", () => {
    expect(
      classifyLocation(`/consultations/${UUID}`, "http://app.example"),
    ).toEqual({
      kind: "consultation",
      destination: { consultationId: UUID, token: null },
    });
  });

  it("classifies a private consultation path with its fragment token", () => {
    expect(
      classifyLocation(
        `/consultations/${UUID}#access=${TOKEN}`,
        "http://app.example",
      ),
    ).toEqual({
      kind: "consultation",
      destination: { consultationId: UUID, token: TOKEN },
    });
  });

  it("classifies a full same-origin consultation URL", () => {
    expect(
      classifyLocation(
        `https://app.example/consultations/${UUID}`,
        "https://app.example",
      ),
    ).toEqual({
      kind: "consultation",
      destination: { consultationId: UUID, token: null },
    });
  });

  it("classifies a malformed consultation path as invalid", () => {
    expect(
      classifyLocation("/consultations/not-a-uuid", "http://app.example"),
    ).toEqual({ kind: "invalid" });
    expect(
      classifyLocation(
        `/consultations/${UUID}?from=feed`,
        "http://app.example",
      ),
    ).toEqual({ kind: "invalid" });
  });

  it("treats unrelated unsupported paths as root, not aliases", () => {
    expect(classifyLocation("/photos/1", "http://app.example")).toEqual({
      kind: "root",
    });
    expect(classifyLocation("/profile", "http://app.example")).toEqual({
      kind: "root",
    });
  });
});

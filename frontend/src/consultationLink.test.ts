import { describe, expect, it } from "vitest";

import {
  buildConsultationPath,
  buildConsultationUrl,
  isValidConsultationId,
  isValidPrivateLinkToken,
  parseConsultationUrl,
  privateLinkHeaders,
  privateLinkRequestOptions,
} from "./consultationLink";

const UUID = "123e4567-e89b-12d3-a456-426614174000";
const TOKEN = `v1.${"A".repeat(43)}`;

describe("isValidConsultationId", () => {
  it("accepts a canonical uuid", () => {
    expect(isValidConsultationId(UUID)).toBe(true);
  });

  it.each([
    ["short", "abc"],
    ["malformed", "not-a-uuid"],
    ["missing", null],
    ["number", 42],
  ])("rejects %s", (_label, value) => {
    expect(isValidConsultationId(value)).toBe(false);
  });
});

describe("isValidPrivateLinkToken", () => {
  it("accepts a well-formed token", () => {
    expect(isValidPrivateLinkToken(TOKEN)).toBe(true);
  });

  it.each([
    ["missing", null],
    ["wrong prefix", `v2.${"A".repeat(43)}`],
    ["short suffix", `v1.${"A".repeat(42)}`],
    ["long suffix", `v1.${"A".repeat(44)}`],
    ["padding", `v1.${"A".repeat(42)}=`],
    ["illegal char", `v1.${"A".repeat(42)}.`],
    ["non string", 42],
  ])("rejects %s", (_label, value) => {
    expect(isValidPrivateLinkToken(value)).toBe(false);
  });
});

describe("buildConsultationPath", () => {
  it("builds a public path without a token", () => {
    expect(buildConsultationPath(UUID)).toBe(`/consultations/${UUID}`);
  });

  it("puts the private token in the fragment", () => {
    expect(buildConsultationPath(UUID, TOKEN)).toBe(
      `/consultations/${UUID}#access=${TOKEN}`,
    );
  });
});

describe("buildConsultationUrl", () => {
  it("prefixes the trusted origin", () => {
    expect(buildConsultationUrl("https://app.example", UUID)).toBe(
      `https://app.example/consultations/${UUID}`,
    );
  });

  it("rejects an untrusted or malformed application origin", () => {
    expect(() => buildConsultationUrl("http://evil.example", UUID)).toThrow(
      "Invalid application origin",
    );
    expect(() =>
      buildConsultationUrl("https://app.example/path", UUID),
    ).toThrow("Invalid application origin");
  });

  it("rejects invalid IDs and tokens when building", () => {
    expect(() => buildConsultationUrl("https://app.example", "bad-id")).toThrow(
      "Invalid consultation ID",
    );
    expect(() =>
      buildConsultationUrl("https://app.example", UUID, "v1.bad"),
    ).toThrow("Invalid private link token");
  });
});

describe("parseConsultationUrl", () => {
  it("parses a public path", () => {
    expect(parseConsultationUrl(`/consultations/${UUID}`)).toEqual({
      consultationId: UUID,
      token: null,
    });
  });

  it("parses a private path with a fragment token", () => {
    expect(
      parseConsultationUrl(`/consultations/${UUID}#access=${TOKEN}`),
    ).toEqual({
      consultationId: UUID,
      token: TOKEN,
    });
  });

  it("parses a full origin URL", () => {
    expect(
      parseConsultationUrl(
        `https://app.example/consultations/${UUID}#access=${TOKEN}`,
        "https://app.example",
      ),
    ).toEqual({ consultationId: UUID, token: TOKEN });
  });

  it("rejects absolute URLs from another origin", () => {
    expect(
      parseConsultationUrl(
        `https://evil.example/consultations/${UUID}#access=${TOKEN}`,
        "https://app.example",
      ),
    ).toBeNull();
  });

  it("requires a trusted origin for an absolute URL", () => {
    expect(
      parseConsultationUrl(
        `https://app.example/consultations/${UUID}#access=${TOKEN}`,
      ),
    ).toBeNull();
  });

  it.each([
    ["wrong path", `/photos/${UUID}`],
    ["trailing slash", `/consultations/${UUID}/`],
    ["query string", `/consultations/${UUID}?from=feed`],
    ["empty", ""],
    ["not a string", 42],
  ])("rejects %s", (_label, value) => {
    expect(parseConsultationUrl(value as string)).toBeNull();
  });

  it.each([
    ["unknown fragment", `#foo=bar`],
    ["duplicate access", `#access=${TOKEN}&access=${TOKEN}`],
    ["extra param", `#access=${TOKEN}&extra=1`],
    ["missing value", `#access=`],
    ["no equals", `#access`],
    ["empty hash", `#`],
    ["oversized token", `#access=${`v1.${"A".repeat(43)}B`}`],
  ])("rejects malformed fragment: %s", (_label, hash) => {
    expect(parseConsultationUrl(`/consultations/${UUID}${hash}`)).toBeNull();
  });
});

describe("privateLinkHeaders", () => {
  it("sends the token header when valid", () => {
    expect(privateLinkHeaders(TOKEN)).toEqual({
      "X-NextPost-Private-Link": TOKEN,
    });
  });

  it("omits the header when there is no token", () => {
    expect(privateLinkHeaders(null)).toEqual({});
  });

  it("omits the header for an invalid token", () => {
    expect(privateLinkHeaders("v1.bad")).toEqual({});
  });
});

describe("privateLinkRequestOptions", () => {
  it("combines the account cookie with a valid private capability", () => {
    expect(privateLinkRequestOptions(TOKEN)).toEqual({
      credentials: "include",
      headers: { "X-NextPost-Private-Link": TOKEN },
    });
  });

  it("keeps credentials but omits a malformed capability", () => {
    expect(privateLinkRequestOptions("v1.bad")).toEqual({
      credentials: "include",
      headers: {},
    });
  });
});

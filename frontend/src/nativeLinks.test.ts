import { describe, expect, it } from "vitest";

import { pathForNativeUrl } from "./nativeLinks";

const UUID = "123e4567-e89b-12d3-a456-426614174000";
const TOKEN = `v1.${"A".repeat(43)}`;

describe("pathForNativeUrl", () => {
  it("accepts canonical public and private consultation links", () => {
    expect(
      pathForNativeUrl(
        `https://nextpost.formcadence.app/consultations/${UUID}`,
      ),
    ).toBe(`/consultations/${UUID}`);
    expect(
      pathForNativeUrl(
        `https://nextpost.formcadence.app/consultations/${UUID}#access=${TOKEN}`,
      ),
    ).toBe(`/consultations/${UUID}#access=${TOKEN}`);
  });

  it("accepts privacy and rejects foreign or unsupported URLs", () => {
    expect(pathForNativeUrl("https://nextpost.formcadence.app/privacy")).toBe(
      "/privacy",
    );
    expect(
      pathForNativeUrl(`https://example.com/consultations/${UUID}`),
    ).toBeNull();
    expect(
      pathForNativeUrl("https://nextpost.formcadence.app/profile"),
    ).toBeNull();
  });
});

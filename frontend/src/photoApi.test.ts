import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { fetchApplicationConfig } from "./photoApi";

const validConfig = {
  consultation_min_photos: 2,
  consultation_max_photos: 10,
  max_open_consultations: 3,
  photo_max_input_bytes: 15728640,
  consultation_question_max_length: 120,
  consultation_context_max_length: 500,
};

function respond(status: number, body: unknown): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      status,
      ok: status >= 200 && status < 300,
      json: () => Promise.resolve(body),
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fetchApplicationConfig", () => {
  it("returns a valid config", async () => {
    respond(200, validConfig);
    await expect(fetchApplicationConfig()).resolves.toEqual(validConfig);
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(fetchApplicationConfig()).rejects.toEqual(
      new ApiError("unauthenticated"),
    );
  });

  it("maps a network failure to network", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("boom")));
    await expect(fetchApplicationConfig()).rejects.toEqual(
      new ApiError("network"),
    );
  });

  it.each([
    [
      "missing question max",
      { ...validConfig, consultation_question_max_length: undefined },
    ],
    [
      "missing context max",
      { ...validConfig, consultation_context_max_length: undefined },
    ],
    [
      "non-finite question max",
      { ...validConfig, consultation_question_max_length: Number.NaN },
    ],
    [
      "non-safe question max",
      {
        ...validConfig,
        consultation_question_max_length: Number.MAX_SAFE_INTEGER + 1,
      },
    ],
    [
      "question max below 27",
      { ...validConfig, consultation_question_max_length: 26 },
    ],
    [
      "zero context max",
      { ...validConfig, consultation_context_max_length: 0 },
    ],
    [
      "negative question max",
      { ...validConfig, consultation_question_max_length: -1 },
    ],
    [
      "string question max",
      { ...validConfig, consultation_question_max_length: "120" },
    ],
  ])("rejects %s as unavailable", async (_label, body) => {
    respond(200, body);
    await expect(fetchApplicationConfig()).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { finalizeConsultation } from "./consultationApi";

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";
const OPERATION_ID = "123e4567-e89b-12d3-a456-426614174001";

const FINAL_RESULT = {
  finalized_at: "2026-09-28T12:05:00Z",
  total_votes: 3,
  declaration: "selected",
  selected_ordinals: [0],
  options: [
    { ordinal: 0, vote_count: 2, selected: true },
    { ordinal: 1, vote_count: 1, selected: false },
  ],
};

function respond(status: number, body: unknown = null): void {
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

describe("finalizeConsultation", () => {
  it("posts the operation id and declaration and resolves on 200", async () => {
    const body = {
      id: CONSULTATION_ID,
      state: "finalized",
      published_at: "2026-09-28T12:00:00Z",
      result: FINAL_RESULT,
    };
    respond(200, body);

    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "selected",
        option_ids: ["123e4567-e89b-12d3-a456-426614174002"],
      }),
    ).resolves.toEqual(body);

    const fetchMock = vi.mocked(globalThis.fetch);
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/my-consultations/${CONSULTATION_ID}/finalize`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          operation_id: OPERATION_ID,
          expected_state: "open",
          declaration: {
            kind: "selected",
            option_ids: ["123e4567-e89b-12d3-a456-426614174002"],
          },
        }),
      }),
    );
  });

  it("resolves a legacy result-unavailable body", async () => {
    respond(200, {
      id: CONSULTATION_ID,
      state: "finalized",
      published_at: "2026-09-28T12:00:00Z",
      result: null,
    });

    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).resolves.toEqual({
      id: CONSULTATION_ID,
      state: "finalized",
      published_at: "2026-09-28T12:00:00Z",
      result: null,
    });
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("unauthenticated"));
  });

  it("maps 409 to consultation_conflict", async () => {
    respond(409, { detail: { code: "consultation_conflict" } });
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("consultation_conflict"));
  });

  it("maps 404 to consultation_unavailable", async () => {
    respond(404, { detail: { code: "consultation_unavailable" } });
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("consultation_unavailable"));
  });

  it("maps 422 invalid_declaration", async () => {
    respond(422, { detail: { code: "invalid_declaration" } });
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("invalid_declaration"));
  });

  it("maps 422 validation_error with field errors", async () => {
    respond(422, {
      detail: {
        code: "validation_error",
        field_errors: { declaration: "bad" },
      },
    });
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("validation_error", { declaration: "bad" }));
  });

  it("maps an unknown error code to unavailable", async () => {
    respond(500, { detail: { code: "server_error" } });
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("server_error"));
  });

  it("rejects a malformed 2xx response", async () => {
    respond(200, {});
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("unavailable"));
  });

  it("maps a network failure to network", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));
    await expect(
      finalizeConsultation(CONSULTATION_ID, OPERATION_ID, {
        kind: "none",
        option_ids: [],
      }),
    ).rejects.toEqual(new ApiError("network"));
  });
});

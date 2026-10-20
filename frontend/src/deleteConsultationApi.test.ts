import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { deleteConsultation } from "./consultationApi";

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";

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

describe("deleteConsultation", () => {
  it("posts the expected state and resolves on 204", async () => {
    respond(204);
    await expect(
      deleteConsultation(CONSULTATION_ID, "open"),
    ).resolves.toBeUndefined();
    const fetchMock = vi.mocked(globalThis.fetch);
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/my-consultations/${CONSULTATION_ID}/delete`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ expected_state: "open" }),
      }),
    );
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(deleteConsultation(CONSULTATION_ID, "open")).rejects.toEqual(
      new ApiError("unauthenticated"),
    );
  });

  it("maps 409 consultation_conflict", async () => {
    respond(409, { detail: { code: "consultation_conflict" } });
    await expect(deleteConsultation(CONSULTATION_ID, "open")).rejects.toEqual(
      new ApiError("consultation_conflict"),
    );
  });

  it("maps 404 consultation_unavailable", async () => {
    respond(404, { detail: { code: "consultation_unavailable" } });
    await expect(deleteConsultation(CONSULTATION_ID, "open")).rejects.toEqual(
      new ApiError("consultation_unavailable"),
    );
  });

  it("maps an unknown error code to unavailable", async () => {
    respond(500, { detail: { code: "server_error" } });
    await expect(deleteConsultation(CONSULTATION_ID, "open")).rejects.toEqual(
      new ApiError("server_error"),
    );
  });

  it("rejects a malformed 2xx response", async () => {
    respond(200, {});
    await expect(deleteConsultation(CONSULTATION_ID, "open")).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("maps a network failure to network", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));
    await expect(deleteConsultation(CONSULTATION_ID, "open")).rejects.toEqual(
      new ApiError("network"),
    );
  });
});

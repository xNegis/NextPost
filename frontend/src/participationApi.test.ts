import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { fetchParticipationHistory } from "./consultationApi";

const UUID = "123e4567-e89b-12d3-a456-426614174000";

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

function validItem(overrides: Record<string, unknown> = {}) {
  return {
    consultation_id: UUID,
    status: "open",
    event_kind: "voted",
    event_at: "2026-10-21T12:00:00Z",
    can_view: true,
    ...overrides,
  };
}

describe("fetchParticipationHistory", () => {
  it("returns a valid participation page", async () => {
    respond(200, { items: [validItem()], next_cursor: null });
    await expect(fetchParticipationHistory()).resolves.toEqual({
      items: [validItem()],
      next_cursor: null,
    });
  });

  it("sends the cursor when provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: () => Promise.resolve({ items: [], next_cursor: null }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchParticipationHistory(20, "abc123");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/my-participation?limit=20&cursor=abc123"),
      { credentials: "include" },
    );
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(fetchParticipationHistory()).rejects.toEqual(
      new ApiError("unauthenticated"),
    );
  });

  it("maps 422 field errors", async () => {
    respond(422, {
      detail: {
        code: "validation_error",
        field_errors: { cursor: "Enter a valid page cursor." },
      },
    });
    await expect(fetchParticipationHistory()).rejects.toEqual(
      new ApiError("validation_error", {
        cursor: "Enter a valid page cursor.",
      }),
    );
  });

  it("maps a network failure to network", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("boom")));
    await expect(fetchParticipationHistory()).rejects.toEqual(
      new ApiError("network"),
    );
  });

  it.each([
    ["open", "voted", true],
    ["open", "voted", false],
    ["matched", "finalized", false],
    ["not_matched", "finalized", false],
    ["no_choice", "finalized", false],
    ["unavailable", "voted", false],
  ] as const)(
    "accepts the semantic combination %s/%s/view=%s",
    async (status, event_kind, can_view) => {
      respond(200, {
        items: [validItem({ status, event_kind, can_view })],
        next_cursor: null,
      });
      await expect(fetchParticipationHistory()).resolves.toMatchObject({
        items: [{ status, event_kind, can_view }],
      });
    },
  );

  it.each([
    ["open", "finalized", false],
    ["matched", "voted", false],
    ["matched", "finalized", true],
    ["not_matched", "finalized", true],
    ["no_choice", "voted", false],
    ["unavailable", "finalized", false],
    ["unavailable", "voted", true],
  ] as const)(
    "rejects the impossible combination %s/%s/view=%s",
    async (status, event_kind, can_view) => {
      respond(200, {
        items: [validItem({ status, event_kind, can_view })],
        next_cursor: null,
      });
      await expect(fetchParticipationHistory()).rejects.toEqual(
        new ApiError("unavailable"),
      );
    },
  );

  it("rejects an unknown status as unavailable", async () => {
    respond(200, {
      items: [validItem({ status: "winner" })],
      next_cursor: null,
    });
    await expect(fetchParticipationHistory()).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects a row with extra forbidden fields", async () => {
    respond(200, {
      items: [{ ...validItem(), photo_id: "leak" }],
      next_cursor: null,
    });
    await expect(fetchParticipationHistory()).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects a non-boolean can_view", async () => {
    respond(200, {
      items: [validItem({ can_view: "yes" })],
      next_cursor: null,
    });
    await expect(fetchParticipationHistory()).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects a malformed event_at", async () => {
    respond(200, {
      items: [validItem({ event_at: "not-a-date" })],
      next_cursor: null,
    });
    await expect(fetchParticipationHistory()).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
});

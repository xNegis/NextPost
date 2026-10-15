import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  fetchConsultationDetail,
  fetchConsultationPhotoUrl,
  fetchFeed,
  fetchMyConsultation,
  fetchMyConsultations,
  publishConsultation,
} from "./consultationApi";

function respond(status: number, body: unknown): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      status,
      ok: status >= 200 && status < 300,
      json: () => Promise.resolve(body),
      blob: () => Promise.resolve(new Blob([body as BlobPart])),
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

const validPublished = {
  id: "123e4567-e89b-12d3-a456-426614174000",
  state: "open",
  audience: "public",
};

describe("publishConsultation", () => {
  it("publishes and returns the consultation", async () => {
    respond(201, validPublished);
    await expect(
      publishConsultation(
        "session-id",
        ["image-1", "image-2"],
        "Which one?",
        null,
        "public",
      ),
    ).resolves.toEqual(validPublished);
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(
      publishConsultation("s", ["a", "b"], "Q", null, "public"),
    ).rejects.toEqual(new ApiError("unauthenticated"));
  });

  it("maps 422 field errors", async () => {
    respond(422, {
      detail: {
        code: "validation_error",
        field_errors: { audience: "Choose an audience." },
      },
    });
    await expect(
      publishConsultation("s", ["a", "b"], "Q", null, "public"),
    ).rejects.toEqual(
      new ApiError("validation_error", { audience: "Choose an audience." }),
    );
  });

  it("maps a cap conflict code", async () => {
    respond(409, { detail: { code: "max_open_consultations_reached" } });
    await expect(
      publishConsultation("s", ["a", "b"], "Q", null, "public"),
    ).rejects.toEqual(new ApiError("max_open_consultations_reached"));
  });

  it("maps a network failure to network", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("boom")));
    await expect(
      publishConsultation("s", ["a", "b"], "Q", null, "public"),
    ).rejects.toEqual(new ApiError("network"));
  });

  it.each(["finalized", "deleted", "removed", "unexpected"])(
    "rejects published state %s as unavailable",
    async (state) => {
      respond(201, { ...validPublished, state });
      await expect(
        publishConsultation("s", ["a", "b"], "Q", null, "public"),
      ).rejects.toEqual(new ApiError("unavailable"));
    },
  );

  it("rejects a missing published state as unavailable", async () => {
    respond(201, { ...validPublished, state: undefined });
    await expect(
      publishConsultation("s", ["a", "b"], "Q", null, "public"),
    ).rejects.toEqual(new ApiError("unavailable"));
  });
});

describe("fetchConsultationDetail", () => {
  const validDetail = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    owner_nickname: "Ana",
    question: "Which one?",
    context: null,
    audience: "public",
    state: "open",
    published_at: "2026-09-28T12:00:00Z",
    photos: [
      { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
    ],
  };

  it("returns a valid detail", async () => {
    respond(200, validDetail);
    await expect(fetchConsultationDetail(validDetail.id)).resolves.toEqual(
      validDetail,
    );
  });

  it("maps unavailable to the server code", async () => {
    respond(404, { detail: { code: "consultation_unavailable" } });
    await expect(fetchConsultationDetail(validDetail.id)).rejects.toEqual(
      new ApiError("consultation_unavailable"),
    );
  });

  it("rejects malformed detail as unavailable", async () => {
    respond(200, { ...validDetail, photos: "not-a-list" });
    await expect(fetchConsultationDetail(validDetail.id)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it.each(["finalized", "deleted", "removed", "unexpected"])(
    "rejects detail state %s as unavailable",
    async (state) => {
      respond(200, { ...validDetail, state });
      await expect(fetchConsultationDetail(validDetail.id)).rejects.toEqual(
        new ApiError("unavailable"),
      );
    },
  );

  it("rejects a missing detail state as unavailable", async () => {
    respond(200, { ...validDetail, state: undefined });
    await expect(fetchConsultationDetail(validDetail.id)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
});

describe("fetchConsultationPhotoUrl", () => {
  it("returns an object URL from a successful blob", async () => {
    respond(200, new Uint8Array([0xff, 0xd8]));
    const url = await fetchConsultationPhotoUrl("c", "p");
    expect(url).toMatch(/^blob:/);
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(fetchConsultationPhotoUrl("c", "p")).rejects.toEqual(
      new ApiError("unauthenticated"),
    );
  });

  it("maps 404 consultation_unavailable distinctly", async () => {
    respond(404, { detail: { code: "consultation_unavailable" } });
    await expect(fetchConsultationPhotoUrl("c", "p")).rejects.toEqual(
      new ApiError("consultation_unavailable"),
    );
  });

  it("maps 503 unavailable to a retryable media error", async () => {
    respond(503, { detail: { code: "unavailable" } });
    await expect(fetchConsultationPhotoUrl("c", "p")).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
});

describe("fetchMyConsultations", () => {
  const openItem = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    state: "open",
    question: "Which one?",
    audience: "public",
    published_at: "2026-09-28T12:00:00Z",
  };
  const finalizedItem = {
    id: "123e4567-e89b-12d3-a456-426614174001",
    state: "finalized",
    published_at: "2026-09-28T12:00:00Z",
  };

  it("returns a valid open list", async () => {
    respond(200, { items: [openItem], next_cursor: null });
    await expect(fetchMyConsultations("open", 20, null)).resolves.toEqual({
      items: [openItem],
      next_cursor: null,
    });
  });

  it("returns a valid finalized list", async () => {
    respond(200, { items: [finalizedItem], next_cursor: "abc" });
    await expect(fetchMyConsultations("finalized", 20, null)).resolves.toEqual({
      items: [finalizedItem],
      next_cursor: "abc",
    });
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(fetchMyConsultations("open", 20, null)).rejects.toEqual(
      new ApiError("unauthenticated"),
    );
  });

  it("maps 422 to validation_error with field errors", async () => {
    respond(422, {
      detail: { code: "validation_error", field_errors: { cursor: "bad" } },
    });
    await expect(fetchMyConsultations("open", 20, "x")).rejects.toEqual(
      new ApiError("validation_error", { cursor: "bad" }),
    );
  });

  it.each([
    { ...openItem, state: "deleted" },
    { ...openItem, id: "not-a-uuid" },
    { ...openItem, audience: "everyone" },
    { ...finalizedItem, question: "leaked" },
    { ...openItem, published_at: 42 },
  ])("rejects malformed item %# as unavailable", async (item) => {
    respond(200, { items: [item], next_cursor: null });
    await expect(fetchMyConsultations("open", 20, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects a non-list next_cursor as unavailable", async () => {
    respond(200, { items: [], next_cursor: 7 });
    await expect(fetchMyConsultations("open", 20, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects a finalized item with an extra key", async () => {
    respond(200, {
      items: [{ ...finalizedItem, generation: "1" }],
      next_cursor: null,
    });
    await expect(fetchMyConsultations("finalized", 20, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it.each([
    "not-a-date",
    "2026",
    "2026-02-30T12:00:00Z",
    "2026-09-28T12:00:00",
    "2026-09-28T12:00:00+02:00",
  ])("rejects invalid or non-UTC timestamp %s", async (published_at) => {
    respond(200, {
      items: [{ ...openItem, published_at }],
      next_cursor: null,
    });
    await expect(fetchMyConsultations("open", 20, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it.each(["a".repeat(600), "not url-safe!"])(
    "rejects an invalid next_cursor %# as unavailable",
    async (cursor) => {
      respond(200, { items: [], next_cursor: cursor });
      await expect(fetchMyConsultations("open", 20, null)).rejects.toEqual(
        new ApiError("unavailable"),
      );
    },
  );

  it("rejects a page with more items than requested", async () => {
    respond(200, { items: [openItem, openItem], next_cursor: null });
    await expect(fetchMyConsultations("open", 1, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects items that do not match the requested state", async () => {
    respond(200, { items: [finalizedItem], next_cursor: null });
    await expect(fetchMyConsultations("open", 20, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
});

describe("fetchMyConsultation", () => {
  const openDetail = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    state: "open",
    owner_nickname: "Ana",
    question: "Which one?",
    context: null,
    audience: "public",
    published_at: "2026-09-28T12:00:00Z",
    photos: [
      { id: "123e4567-e89b-12d3-a456-426614174002", width: 64, height: 64 },
    ],
  };
  const finalizedDetail = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    state: "finalized",
    published_at: "2026-09-28T12:00:00Z",
  };

  it("returns a valid open detail", async () => {
    respond(200, openDetail);
    await expect(fetchMyConsultation(openDetail.id)).resolves.toEqual(
      openDetail,
    );
  });

  it("returns a valid finalized detail", async () => {
    respond(200, finalizedDetail);
    await expect(fetchMyConsultation(finalizedDetail.id)).resolves.toEqual(
      finalizedDetail,
    );
  });

  it("maps 404 to consultation_unavailable", async () => {
    respond(404, { detail: { code: "consultation_unavailable" } });
    await expect(fetchMyConsultation(openDetail.id)).rejects.toEqual(
      new ApiError("consultation_unavailable"),
    );
  });

  it.each([
    { ...finalizedDetail, question: "leaked" },
    { ...finalizedDetail, photos: [] },
    { ...openDetail, state: "deleted" },
    { ...openDetail, photos: "nope" },
  ])(
    "rejects forbidden or malformed detail %# as unavailable",
    async (detail) => {
      respond(200, detail);
      await expect(fetchMyConsultation(detail.id)).rejects.toEqual(
        new ApiError("unavailable"),
      );
    },
  );

  it.each([0, -1, 1.5, "64", Number.MAX_SAFE_INTEGER + 1])(
    "rejects an invalid photo dimension %# as unavailable",
    async (dimension) => {
      respond(200, {
        ...openDetail,
        photos: [{ ...openDetail.photos[0], width: dimension }],
      });
      await expect(fetchMyConsultation(openDetail.id)).rejects.toEqual(
        new ApiError("unavailable"),
      );
    },
  );

  it("rejects a detail whose id does not match the requested id", async () => {
    respond(200, {
      ...finalizedDetail,
      id: "123e4567-e89b-12d3-a456-426614174999",
    });
    await expect(fetchMyConsultation(openDetail.id)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
  it.each([
    { id: "not-a-uuid", width: 64, height: 64 },
    {
      id: "123e4567-e89b-12d3-a456-426614174002",
      width: 64,
      height: 64,
      storage_key: "private",
    },
  ])("rejects malformed owner photo metadata %#", async (photo) => {
    respond(200, { ...openDetail, photos: [photo] });
    await expect(fetchMyConsultation(openDetail.id)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
});

describe("fetchConsultationDetail tightened validation", () => {
  const validDetail = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    owner_nickname: "Ana",
    question: "Which one?",
    context: null,
    audience: "public",
    state: "open",
    published_at: "2026-09-28T12:00:00Z",
    photos: [
      { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
    ],
  };

  it.each([
    { ...validDetail, photos: [{ id: "not-a-uuid", width: 64, height: 64 }] },
    {
      ...validDetail,
      photos: [
        { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
        { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
      ],
    },
    { ...validDetail, audience: "everyone" },
    { ...validDetail, extra: "nope" },
  ])(
    "rejects malformed or leaking detail %# as unavailable",
    async (detail) => {
      respond(200, detail);
      await expect(fetchConsultationDetail(validDetail.id)).rejects.toEqual(
        new ApiError("unavailable"),
      );
    },
  );

  it("rejects a detail whose id does not match the requested id", async () => {
    respond(200, validDetail);
    await expect(
      fetchConsultationDetail("123e4567-e89b-12d3-a456-426614174999"),
    ).rejects.toEqual(new ApiError("unavailable"));
  });
});

describe("fetchFeed", () => {
  const feedItem = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    owner_nickname: "Ana",
    question: "Which one?",
    context_excerpt: "Context",
    audience: "public",
    state: "open",
    published_at: "2026-09-28T12:00:00Z",
    is_owner: false,
    first_photo: {
      id: "123e4567-e89b-12d3-a456-426614174001",
      width: 64,
      height: 64,
    },
  };

  it("returns a valid feed page", async () => {
    respond(200, { items: [feedItem], next_cursor: "abc" });
    await expect(fetchFeed(20, null)).resolves.toEqual({
      items: [feedItem],
      next_cursor: "abc",
    });
  });

  it("maps 401 to unauthenticated", async () => {
    respond(401, { detail: { code: "unauthenticated" } });
    await expect(fetchFeed(20, null)).rejects.toEqual(
      new ApiError("unauthenticated"),
    );
  });

  it("maps 422 to validation_error with field errors", async () => {
    respond(422, {
      detail: { code: "validation_error", field_errors: { cursor: "bad" } },
    });
    await expect(fetchFeed(20, "x")).rejects.toEqual(
      new ApiError("validation_error", { cursor: "bad" }),
    );
  });

  it.each([
    { ...feedItem, state: "finalized" },
    { ...feedItem, audience: "private" },
    { ...feedItem, is_owner: "yes" },
    { ...feedItem, first_photo: { ...feedItem.first_photo, width: 0 } },
    { ...feedItem, id: "not-a-uuid" },
    { ...feedItem, context_excerpt: 42 },
  ])("rejects malformed feed item %# as unavailable", async (item) => {
    respond(200, { items: [item], next_cursor: null });
    await expect(fetchFeed(20, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects a page with more items than requested", async () => {
    respond(200, { items: [feedItem, feedItem], next_cursor: null });
    await expect(fetchFeed(1, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });

  it("rejects a malformed next_cursor as unavailable", async () => {
    respond(200, { items: [], next_cursor: 7 });
    await expect(fetchFeed(20, null)).rejects.toEqual(
      new ApiError("unavailable"),
    );
  });
});

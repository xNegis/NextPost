import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  createAccount,
  fetchProfile,
  fetchSession,
  signIn,
  signOut,
} from "./api";

interface FakeResponse {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
}

function stubFetch(response: FakeResponse) {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function jsonResponse(status: number, body: unknown): FakeResponse {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fetchSession", () => {
  it("returns unauthenticated on a 401 response", async () => {
    stubFetch(jsonResponse(401, { detail: { code: "unauthenticated" } }));

    await expect(fetchSession()).resolves.toEqual({ authenticated: false });
  });

  it("returns the account on a valid authenticated response", async () => {
    stubFetch(
      jsonResponse(200, {
        authenticated: true,
        account: { id: "1", alias: "Ana" },
      }),
    );

    await expect(fetchSession()).resolves.toEqual({
      authenticated: true,
      account: { id: "1", alias: "Ana" },
    });
  });

  it("rejects an invalid authenticated body", async () => {
    stubFetch(
      jsonResponse(200, { authenticated: true, account: { alias: "Ana" } }),
    );

    await expect(fetchSession()).rejects.toMatchObject({ code: "unavailable" });
  });

  it("maps a network failure to a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(fetchSession()).rejects.toMatchObject({ code: "network" });
  });
});

describe("createAccount", () => {
  it("posts credentials and returns the account summary", async () => {
    const fetchMock = stubFetch(jsonResponse(201, { id: "1", alias: "Ana" }));

    await expect(
      createAccount({
        email: "ana@example.com",
        alias: "Ana",
        password: "correct-horse-battery-staple",
      }),
    ).resolves.toEqual({ id: "1", alias: "Ana" });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/accounts");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    expect(JSON.parse(init.body as string)).toEqual({
      email: "ana@example.com",
      alias: "Ana",
      password: "correct-horse-battery-staple",
    });
  });

  it("maps a duplicate alias to an alias_unavailable error", async () => {
    stubFetch(jsonResponse(409, { detail: { code: "alias_unavailable" } }));

    const error = await createAccount({
      email: "ana@example.com",
      alias: "Ana",
      password: "correct-horse-battery-staple",
    }).catch((value: unknown) => value);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("alias_unavailable");
  });

  it("maps a duplicate email to a generic registration error", async () => {
    stubFetch(
      jsonResponse(409, { detail: { code: "registration_unavailable" } }),
    );

    const error = await createAccount({
      email: "ana@example.com",
      alias: "Ana",
      password: "correct-horse-battery-staple",
    }).catch((value: unknown) => value);

    expect((error as ApiError).code).toBe("registration_unavailable");
  });

  it("maps validation errors to field errors", async () => {
    stubFetch(
      jsonResponse(422, {
        detail: {
          code: "validation_error",
          field_errors: { email: "Enter a valid email address." },
        },
      }),
    );

    const error = await createAccount({
      email: "nope",
      alias: "Ana",
      password: "correct-horse-battery-staple",
    }).catch((value: unknown) => value);

    expect((error as ApiError).code).toBe("validation_error");
    expect((error as ApiError).fieldErrors).toEqual({
      email: "Enter a valid email address.",
    });
  });

  it("maps an unexpected server error to an unavailable error", async () => {
    stubFetch(jsonResponse(500, {}));

    await expect(
      createAccount({
        email: "ana@example.com",
        alias: "Ana",
        password: "correct-horse-battery-staple",
      }),
    ).rejects.toMatchObject({ code: "unavailable" });
  });
});

describe("signIn", () => {
  it("posts credentials and returns the account summary", async () => {
    const fetchMock = stubFetch(jsonResponse(200, { id: "1", alias: "Ana" }));

    await expect(
      signIn({
        email: "ana@example.com",
        password: "correct-horse-battery-staple",
      }),
    ).resolves.toEqual({ id: "1", alias: "Ana" });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/session");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    expect(JSON.parse(init.body as string)).toEqual({
      email: "ana@example.com",
      password: "correct-horse-battery-staple",
    });
  });

  it("maps a 401 to an invalid_credentials error", async () => {
    stubFetch(jsonResponse(401, { detail: { code: "invalid_credentials" } }));

    const error = await signIn({
      email: "ana@example.com",
      password: "wrong",
    }).catch((value: unknown) => value);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("invalid_credentials");
  });

  it("maps validation errors to field errors", async () => {
    stubFetch(
      jsonResponse(422, {
        detail: {
          code: "validation_error",
          field_errors: { email: "Enter a valid email address." },
        },
      }),
    );

    const error = await signIn({
      email: "nope",
      password: "correct-horse-battery-staple",
    }).catch((value: unknown) => value);

    expect((error as ApiError).code).toBe("validation_error");
    expect((error as ApiError).fieldErrors).toEqual({
      email: "Enter a valid email address.",
    });
  });

  it("rejects an invalid success body", async () => {
    stubFetch(jsonResponse(200, { alias: "Ana" }));

    await expect(
      signIn({
        email: "ana@example.com",
        password: "correct-horse-battery-staple",
      }),
    ).rejects.toMatchObject({ code: "unavailable" });
  });

  it("maps an unexpected server error to an unavailable error", async () => {
    stubFetch(jsonResponse(500, {}));

    await expect(
      signIn({
        email: "ana@example.com",
        password: "correct-horse-battery-staple",
      }),
    ).rejects.toMatchObject({ code: "unavailable" });
  });

  it("maps a network failure to a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(
      signIn({
        email: "ana@example.com",
        password: "correct-horse-battery-staple",
      }),
    ).rejects.toMatchObject({ code: "network" });
  });
});

describe("signOut", () => {
  it("deletes the session with credentials and resolves on success", async () => {
    const fetchMock = stubFetch({
      ok: true,
      status: 204,
      json: async () => {
        throw new Error("no body");
      },
    });

    await expect(signOut()).resolves.toBeUndefined();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/session");
    expect(init.method).toBe("DELETE");
    expect(init.credentials).toBe("include");
  });

  it("maps an unexpected server error to an unavailable error", async () => {
    stubFetch(jsonResponse(500, {}));

    await expect(signOut()).rejects.toMatchObject({ code: "unavailable" });
  });

  it("maps a network failure to a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(signOut()).rejects.toMatchObject({ code: "network" });
  });
});

describe("fetchProfile", () => {
  it("requests the profile with credentials and returns email and nickname", async () => {
    const fetchMock = stubFetch(
      jsonResponse(200, { email: "ana@example.com", nickname: "Ana" }),
    );

    await expect(fetchProfile()).resolves.toEqual({
      email: "ana@example.com",
      nickname: "Ana",
    });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/profile");
    expect(init.method).toBeUndefined();
    expect(init.credentials).toBe("include");
  });

  it("rejects a success body missing required fields", async () => {
    stubFetch(jsonResponse(200, { email: "ana@example.com" }));

    await expect(fetchProfile()).rejects.toMatchObject({ code: "unavailable" });
  });

  it("rejects a success body with wrong field types", async () => {
    stubFetch(jsonResponse(200, { email: 42, nickname: "Ana" }));

    await expect(fetchProfile()).rejects.toMatchObject({ code: "unavailable" });
  });

  it("rejects a success body with unexpected fields", async () => {
    stubFetch(
      jsonResponse(200, {
        email: "ana@example.com",
        nickname: "Ana",
        id: "private-account-id",
      }),
    );

    await expect(fetchProfile()).rejects.toMatchObject({ code: "unavailable" });
  });

  it("maps a 401 response to an unauthenticated error", async () => {
    stubFetch(jsonResponse(401, { detail: { code: "unauthenticated" } }));

    await expect(fetchProfile()).rejects.toMatchObject({
      code: "unauthenticated",
    });
  });

  it("maps an unexpected server error to an unavailable error", async () => {
    stubFetch(jsonResponse(500, {}));

    await expect(fetchProfile()).rejects.toMatchObject({ code: "unavailable" });
  });

  it("maps a network failure to a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(fetchProfile()).rejects.toMatchObject({ code: "network" });
  });
});

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { fetchMyConsultationResults } from "./consultationApi";
import { useOwnerConsultationResults } from "./useOwnerConsultationResults";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return { ...actual, fetchMyConsultationResults: vi.fn() };
});

const resultsMock = vi.mocked(fetchMyConsultationResults);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";
const NEXT_ID = "123e4567-e89b-12d3-a456-426614174999";

function result(id = CONSULTATION_ID, total = 1) {
  return {
    consultation_id: id,
    state: "open" as const,
    total_votes: total,
    options: [
      {
        photo_id: "123e4567-e89b-12d3-a456-426614174001",
        ordinal: 0,
        vote_count: total,
      },
    ],
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  resultsMock.mockResolvedValue(result());
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

function setup(id = CONSULTATION_ID, enabled = true, onSessionLost = vi.fn()) {
  return renderHook(
    ({ enabled, id, onSessionLost }) =>
      useOwnerConsultationResults(id, enabled, onSessionLost),
    { initialProps: { enabled, id, onSessionLost } },
  );
}

describe("useOwnerConsultationResults", () => {
  it("loads immediately when enabled", async () => {
    setup();
    await waitFor(() => expect(resultsMock).toHaveBeenCalledTimes(1));
  });

  it("refreshes every five seconds while enabled", async () => {
    vi.useFakeTimers();
    setup();
    await act(async () => {});
    expect(resultsMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(resultsMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(resultsMock).toHaveBeenCalledTimes(3);
  });

  it("reports an error on a failed first load instead of zero", async () => {
    resultsMock.mockRejectedValue(new Error("offline"));
    const view = setup();
    await waitFor(() =>
      expect(view.result.current.phase).toEqual({ kind: "error" }),
    );
  });

  it("preserves last-known counts and marks them stale on refresh failure", async () => {
    vi.useFakeTimers();
    const view = setup();
    await act(async () => {});
    expect(view.result.current.phase.kind).toBe("ready");

    resultsMock.mockRejectedValueOnce(new Error("offline"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(view.result.current.phase).toMatchObject({
      kind: "ready",
      stale: true,
    });
    expect(
      view.result.current.phase.kind === "ready" &&
        view.result.current.phase.result.total_votes,
    ).toBe(1);
  });

  it("does not overlap a slow in-flight request", async () => {
    vi.useFakeTimers();
    let resolveSlow: (value: unknown) => void = () => undefined;
    resultsMock.mockResolvedValueOnce(result());
    resultsMock.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveSlow = resolve;
      }),
    );
    setup();
    await act(async () => {});
    expect(resultsMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(resultsMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(resultsMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      resolveSlow(result());
    });
  });

  it("delegates session loss", async () => {
    const onSessionLost = vi.fn();
    resultsMock.mockRejectedValue(new ApiError("unauthenticated"));
    setup(CONSULTATION_ID, true, onSessionLost);
    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });

  it("shows unavailable and stops polling after a generic denial", async () => {
    vi.useFakeTimers();
    resultsMock.mockRejectedValue(new ApiError("consultation_unavailable"));
    const view = setup();
    await act(async () => {});
    expect(view.result.current.phase).toEqual({ kind: "unavailable" });
    expect(resultsMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(15000);
    });
    expect(resultsMock).toHaveBeenCalledTimes(1);
  });

  it("pauses while hidden and refreshes immediately when visible again", async () => {
    vi.useFakeTimers();
    let visibility: DocumentVisibilityState = "visible";
    vi.spyOn(document, "visibilityState", "get").mockImplementation(
      () => visibility,
    );
    setup();
    await act(async () => {});
    expect(resultsMock).toHaveBeenCalledTimes(1);

    visibility = "hidden";
    document.dispatchEvent(new Event("visibilitychange"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(15000);
    });
    expect(resultsMock).toHaveBeenCalledTimes(1);

    visibility = "visible";
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(resultsMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(4999);
    });
    expect(resultsMock).toHaveBeenCalledTimes(2);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(resultsMock).toHaveBeenCalledTimes(3);
  });

  it("clears to idle and stops when disabled", async () => {
    vi.useFakeTimers();
    const view = setup();
    await act(async () => {});
    expect(view.result.current.phase.kind).toBe("ready");

    view.rerender({
      enabled: false,
      id: CONSULTATION_ID,
      onSessionLost: vi.fn(),
    });
    expect(view.result.current.phase).toEqual({ kind: "idle" });

    const calls = resultsMock.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(15000);
    });
    expect(resultsMock.mock.calls.length).toBe(calls);
  });

  it("ignores a late response for a previous consultation", async () => {
    let resolveFirst: (value: unknown) => void = () => undefined;
    resultsMock.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveFirst = resolve;
      }),
    );
    const view = setup();
    resultsMock.mockResolvedValueOnce(result(NEXT_ID, 2));

    view.rerender({ enabled: true, id: NEXT_ID, onSessionLost: vi.fn() });
    await waitFor(() =>
      expect(view.result.current.phase).toMatchObject({
        kind: "ready",
        result: { consultation_id: NEXT_ID },
      }),
    );

    await act(async () => {
      resolveFirst(result(CONSULTATION_ID, 1));
    });
    expect(view.result.current.phase).toMatchObject({
      kind: "ready",
      result: { consultation_id: NEXT_ID },
    });
  });
});

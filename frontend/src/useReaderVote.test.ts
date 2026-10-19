import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { fetchMyVote, submitVote } from "./consultationApi";
import { useReaderVote } from "./useReaderVote";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchMyVote: vi.fn(),
    submitVote: vi.fn(),
  };
});

const myVoteMock = vi.mocked(fetchMyVote);
const submitVoteMock = vi.mocked(submitVote);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";
const PHOTO_A = "123e4567-e89b-12d3-a456-426614174001";
const PHOTO_B = "123e4567-e89b-12d3-a456-426614174002";
const OLD_TOKEN = `v1.${"A".repeat(43)}`;
const CURRENT_TOKEN = `v1.${"B".repeat(43)}`;

beforeEach(() => {
  vi.clearAllMocks();
  myVoteMock.mockResolvedValue({ status: "not_voted" });
  submitVoteMock.mockResolvedValue({ status: "voted", photo_id: PHOTO_A });
});

describe("useReaderVote", () => {
  it("submits and records the confirmed vote", async () => {
    const { result } = renderHook(() =>
      useReaderVote(CONSULTATION_ID, null, vi.fn()),
    );

    await waitFor(() =>
      expect(result.current.status).toEqual({ kind: "not_voted" }),
    );

    await act(async () => {
      await result.current.submit(PHOTO_A);
    });

    expect(result.current.status).toEqual({ kind: "voted", photoId: PHOTO_A });
    expect(submitVoteMock).toHaveBeenCalledWith(CONSULTATION_ID, PHOTO_A, null);
  });

  it("recovers the authoritative choice after a different-option conflict", async () => {
    submitVoteMock.mockRejectedValue(new ApiError("vote_already_recorded"));
    myVoteMock
      .mockResolvedValueOnce({ status: "not_voted" })
      .mockResolvedValueOnce({ status: "voted", photo_id: PHOTO_B });

    const { result } = renderHook(() =>
      useReaderVote(CONSULTATION_ID, null, vi.fn()),
    );
    await waitFor(() =>
      expect(result.current.status).toEqual({ kind: "not_voted" }),
    );

    await act(async () => {
      await result.current.submit(PHOTO_A);
    });

    expect(result.current.status).toEqual({ kind: "voted", photoId: PHOTO_B });
  });

  it("keeps the reviewed choice retryable when a lost POST recorded nothing", async () => {
    submitVoteMock.mockRejectedValue(new ApiError("network"));
    myVoteMock.mockResolvedValue({ status: "not_voted" });

    const { result } = renderHook(() =>
      useReaderVote(CONSULTATION_ID, null, vi.fn()),
    );
    await waitFor(() =>
      expect(result.current.status).toEqual({ kind: "not_voted" }),
    );

    await act(async () => {
      await result.current.submit(PHOTO_A);
    });

    expect(result.current.outcome).toBe("retryable");
    expect(result.current.status).toEqual({ kind: "not_voted" });
    expect(result.current.submitting).toBe(false);
  });

  it("reports an unknown outcome when both the POST and reconciliation fail", async () => {
    submitVoteMock.mockRejectedValue(new ApiError("network"));
    myVoteMock
      .mockResolvedValueOnce({ status: "not_voted" })
      .mockRejectedValueOnce(new Error("offline"));

    const { result } = renderHook(() =>
      useReaderVote(CONSULTATION_ID, null, vi.fn()),
    );
    await waitFor(() =>
      expect(result.current.status).toEqual({ kind: "not_voted" }),
    );

    await act(async () => {
      await result.current.submit(PHOTO_A);
    });

    expect(result.current.outcome).toBe("unknown");
  });

  it("delegates session loss from submission to the parent", async () => {
    const onSessionLost = vi.fn();
    submitVoteMock.mockRejectedValue(new ApiError("unauthenticated"));

    const { result } = renderHook(() =>
      useReaderVote(CONSULTATION_ID, null, onSessionLost),
    );
    await waitFor(() =>
      expect(result.current.status).toEqual({ kind: "not_voted" }),
    );

    await act(async () => {
      await result.current.submit(PHOTO_A);
    });

    expect(onSessionLost).toHaveBeenCalledTimes(1);
  });

  it("marks the status unavailable on denial", async () => {
    myVoteMock.mockRejectedValue(new ApiError("consultation_unavailable"));

    const { result } = renderHook(() =>
      useReaderVote(CONSULTATION_ID, null, vi.fn()),
    );

    await waitFor(() =>
      expect(result.current.status).toEqual({ kind: "unavailable" }),
    );
  });

  it("rechecks authorization when the Private token changes", async () => {
    const { rerender } = renderHook(
      ({ token }) => useReaderVote(CONSULTATION_ID, token, vi.fn()),
      { initialProps: { token: OLD_TOKEN } },
    );

    await waitFor(() =>
      expect(myVoteMock).toHaveBeenCalledWith(CONSULTATION_ID, OLD_TOKEN),
    );
    rerender({ token: CURRENT_TOKEN });
    await waitFor(() =>
      expect(myVoteMock).toHaveBeenLastCalledWith(
        CONSULTATION_ID,
        CURRENT_TOKEN,
      ),
    );
  });
});

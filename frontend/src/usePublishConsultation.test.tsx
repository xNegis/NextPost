import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { publishConsultation } from "./consultationApi";
import { usePublishConsultation } from "./usePublishConsultation";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return { ...actual, publishConsultation: vi.fn() };
});

const publishConsultationMock = vi.mocked(publishConsultation);

const snapshot = {
  sessionId: "session-id",
  orderedImageIds: ["image-1", "image-2"],
  question: "Which one?",
  context: null,
  audience: "public" as const,
};

const published = {
  id: "123e4567-e89b-12d3-a456-426614174000",
  state: "open" as const,
  audience: "public",
};

beforeEach(() => {
  publishConsultationMock.mockReset();
});

describe("usePublishConsultation", () => {
  it("starts idle", () => {
    const { result } = renderHook(() =>
      usePublishConsultation(() => undefined),
    );
    expect(result.current.status).toBe("idle");
    expect(result.current.published).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("publishes and reports success", async () => {
    publishConsultationMock.mockResolvedValue(published);
    const { result } = renderHook(() =>
      usePublishConsultation(() => undefined),
    );

    act(() => result.current.publish(snapshot));
    expect(result.current.status).toBe("pending");

    await waitFor(() => expect(result.current.status).toBe("success"));
    expect(result.current.published).toEqual(published);
    expect(result.current.error).toBeNull();
  });

  it("prevents duplicate activation while pending", async () => {
    let resolvePublish: (value: typeof published) => void = () => undefined;
    publishConsultationMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePublish = resolve;
        }),
    );
    const { result } = renderHook(() =>
      usePublishConsultation(() => undefined),
    );

    act(() => result.current.publish(snapshot));
    act(() => result.current.publish(snapshot));

    expect(publishConsultationMock).toHaveBeenCalledTimes(1);

    act(() => resolvePublish(published));
    await waitFor(() => expect(result.current.status).toBe("success"));
  });

  it("retries the same frozen snapshot", async () => {
    publishConsultationMock
      .mockRejectedValueOnce(new ApiError("network"))
      .mockResolvedValueOnce(published);
    const { result } = renderHook(() =>
      usePublishConsultation(() => undefined),
    );

    act(() => result.current.publish(snapshot));
    await waitFor(() => expect(result.current.status).toBe("error"));

    act(() => result.current.retry());
    await waitFor(() => expect(result.current.status).toBe("success"));

    expect(publishConsultationMock).toHaveBeenCalledTimes(2);
    expect(publishConsultationMock).toHaveBeenLastCalledWith(
      snapshot.sessionId,
      snapshot.orderedImageIds,
      snapshot.question,
      snapshot.context,
      snapshot.audience,
    );
  });

  it("preserves distinguishable error codes", async () => {
    publishConsultationMock.mockRejectedValue(
      new ApiError("max_open_consultations_reached"),
    );
    const { result } = renderHook(() =>
      usePublishConsultation(() => undefined),
    );

    act(() => result.current.publish(snapshot));
    await waitFor(() => expect(result.current.status).toBe("error"));

    expect(result.current.error?.code).toBe("max_open_consultations_reached");
  });

  it("delegates session loss on 401", async () => {
    publishConsultationMock.mockRejectedValue(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();
    const { result } = renderHook(() => usePublishConsultation(onSessionLost));

    act(() => result.current.publish(snapshot));
    await waitFor(() => expect(result.current.status).toBe("error"));

    expect(onSessionLost).toHaveBeenCalledTimes(1);
  });

  it("reset clears state", async () => {
    publishConsultationMock.mockResolvedValue(published);
    const { result } = renderHook(() =>
      usePublishConsultation(() => undefined),
    );

    act(() => result.current.publish(snapshot));
    await waitFor(() => expect(result.current.status).toBe("success"));
    act(() => result.current.reset());

    expect(result.current.status).toBe("idle");
    expect(result.current.published).toBeNull();
    expect(result.current.error).toBeNull();
  });
});

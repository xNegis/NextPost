import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { fetchConsultationPhotoUrl, type FeedItem } from "./consultationApi";
import { useFeedPreviews } from "./useFeedPreviews";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchConsultationPhotoUrl: vi.fn(),
  };
});

const photoMock = vi.mocked(fetchConsultationPhotoUrl);

let observerCallback: IntersectionObserverCallback | null = null;

class MockIntersectionObserver {
  callback: IntersectionObserverCallback;
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
    observerCallback = callback;
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}

function makeItem(index: number): FeedItem {
  const hex = index.toString(16).padStart(12, "0");
  return {
    id: `123e4567-e89b-12d3-a456-4266${hex}`,
    owner_nickname: "Ana",
    question: `Question ${index}`,
    context_excerpt: null,
    audience: "public",
    state: "open",
    published_at: "2026-09-28T12:00:00Z",
    is_owner: false,
    has_voted: false,
    first_photo: {
      id: `223e4567-e89b-12d3-a456-4266${hex}`,
      width: 64,
      height: 64,
    },
  };
}

function makeCard(id: string): HTMLElement {
  const element = document.createElement("div");
  element.setAttribute("data-feed-card", id);
  return element;
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function fireVisibility(
  entries: Array<{ element: HTMLElement; isIntersecting: boolean }>,
) {
  if (observerCallback === null) throw new Error("observer not created");
  act(() => {
    observerCallback!(
      entries.map((entry) => ({
        target: entry.element,
        isIntersecting: entry.isIntersecting,
      })) as IntersectionObserverEntry[],
      {} as IntersectionObserver,
    );
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  observerCallback = null;
  vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useFeedPreviews", () => {
  it("bounds concurrent preview requests to four", async () => {
    const items = [
      makeItem(0),
      makeItem(1),
      makeItem(2),
      makeItem(3),
      makeItem(4),
    ];
    const resolvers: Array<(url: string) => void> = [];
    photoMock.mockImplementation(
      () => new Promise<string>((resolve) => resolvers.push(resolve)),
    );

    const { result } = renderHook(() => useFeedPreviews(items, true, vi.fn()));
    const elements = items.map((item) => makeCard(item.id));

    act(() => {
      items.forEach((item, index) =>
        result.current.observe(item.id, elements[index]),
      );
    });
    fireVisibility(
      elements.map((element) => ({ element, isIntersecting: true })),
    );

    await waitFor(() => expect(photoMock).toHaveBeenCalledTimes(4));

    act(() => {
      resolvers[0]("blob:0");
    });
    await waitFor(() => expect(photoMock).toHaveBeenCalledTimes(5));
  });

  it("revokes the object URL when the feed unmounts", async () => {
    const items = [makeItem(0)];
    photoMock.mockResolvedValue("blob:revoked");
    const revoke = vi.spyOn(URL, "revokeObjectURL");

    const { result, unmount } = renderHook(() =>
      useFeedPreviews(items, true, vi.fn()),
    );
    const element = makeCard(items[0].id);

    act(() => {
      result.current.observe(items[0].id, element);
    });
    fireVisibility([{ element, isIntersecting: true }]);
    await waitFor(() =>
      expect(result.current.stateFor(items[0].id).kind).toBe("ready"),
    );

    act(() => unmount());
    expect(revoke).toHaveBeenCalledWith("blob:revoked");
    revoke.mockRestore();
  });

  it("revokes the URL when a card leaves visibility", async () => {
    const items = [makeItem(0)];
    photoMock.mockResolvedValue("blob:visible");
    const revoke = vi.spyOn(URL, "revokeObjectURL");

    const { result } = renderHook(() => useFeedPreviews(items, true, vi.fn()));
    const element = makeCard(items[0].id);

    act(() => {
      result.current.observe(items[0].id, element);
    });
    fireVisibility([{ element, isIntersecting: true }]);
    await waitFor(() =>
      expect(result.current.stateFor(items[0].id).kind).toBe("ready"),
    );

    fireVisibility([{ element, isIntersecting: false }]);
    expect(result.current.stateFor(items[0].id).kind).toBe("idle");
    expect(revoke).toHaveBeenCalledWith("blob:visible");
    revoke.mockRestore();
  });

  it("marks a denied preview card as denied without a URL", async () => {
    const items = [makeItem(0)];
    photoMock.mockRejectedValue(new ApiError("consultation_unavailable"));

    const { result } = renderHook(() => useFeedPreviews(items, true, vi.fn()));
    const element = makeCard(items[0].id);

    act(() => {
      result.current.observe(items[0].id, element);
    });
    fireVisibility([{ element, isIntersecting: true }]);

    await waitFor(() =>
      expect(result.current.stateFor(items[0].id).kind).toBe("denied"),
    );
  });

  it("retries a failed preview after a local retry", async () => {
    const items = [makeItem(0)];
    photoMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce("blob:retried");

    const { result } = renderHook(() => useFeedPreviews(items, true, vi.fn()));
    const element = makeCard(items[0].id);

    act(() => {
      result.current.observe(items[0].id, element);
    });
    fireVisibility([{ element, isIntersecting: true }]);
    await waitFor(() =>
      expect(result.current.stateFor(items[0].id).kind).toBe("error"),
    );

    act(() => result.current.retry(items[0].id));
    await waitFor(() =>
      expect(result.current.stateFor(items[0].id).kind).toBe("ready"),
    );
  });

  it("ignores a preview 401 received after unmount", async () => {
    const request = deferred<string>();
    photoMock.mockReturnValue(request.promise);
    const lost = vi.fn();
    const items = [makeItem(0)];

    const { result, unmount } = renderHook(() =>
      useFeedPreviews(items, true, lost),
    );
    const element = makeCard(items[0].id);
    act(() => result.current.observe(items[0].id, element));
    fireVisibility([{ element, isIntersecting: true }]);
    await waitFor(() => expect(photoMock).toHaveBeenCalledTimes(1));

    act(() => unmount());
    await act(async () => {
      request.reject(new ApiError("unauthenticated"));
      await Promise.resolve();
    });
    expect(lost).not.toHaveBeenCalled();
  });

  it("revokes an old preview response after a newer visibility scope", async () => {
    const old = deferred<string>();
    const current = deferred<string>();
    photoMock
      .mockReturnValueOnce(old.promise)
      .mockReturnValueOnce(current.promise);
    const revoke = vi.spyOn(URL, "revokeObjectURL");
    const items = [makeItem(0)];

    const { result, rerender } = renderHook(
      ({ active }) => useFeedPreviews(items, active, vi.fn()),
      { initialProps: { active: true } },
    );
    const element = makeCard(items[0].id);
    act(() => result.current.observe(items[0].id, element));
    fireVisibility([{ element, isIntersecting: true }]);

    rerender({ active: false });
    rerender({ active: true });
    act(() => result.current.observe(items[0].id, element));
    fireVisibility([{ element, isIntersecting: true }]);
    await waitFor(() => expect(photoMock).toHaveBeenCalledTimes(2));

    await act(async () => {
      current.resolve("blob:new");
    });
    await act(async () => {
      old.resolve("blob:old");
    });

    expect(result.current.stateFor(items[0].id)).toEqual({
      kind: "ready",
      url: "blob:new",
    });
    expect(revoke).toHaveBeenCalledWith("blob:old");
    revoke.mockRestore();
  });
});

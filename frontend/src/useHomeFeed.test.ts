import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { fetchFeed, type FeedItem } from "./consultationApi";
import { useHomeFeed } from "./useHomeFeed";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return { ...actual, fetchFeed: vi.fn() };
});

const feedMock = vi.mocked(fetchFeed);

const ITEM: FeedItem = {
  id: "123e4567-e89b-12d3-a456-426614174000",
  owner_nickname: "Ana",
  question: "Question",
  context_excerpt: null,
  audience: "public",
  state: "open",
  published_at: "2026-09-28T12:00:00Z",
  is_owner: false,
  has_voted: false,
  first_photo: {
    id: "123e4567-e89b-12d3-a456-426614174001",
    width: 64,
    height: 64,
  },
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

beforeEach(() => {
  vi.clearAllMocks();
  feedMock.mockResolvedValue({ items: [], next_cursor: null });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useHomeFeed", () => {
  it("explicit Refresh reads one newest page after loading more", async () => {
    feedMock
      .mockResolvedValueOnce({ items: [ITEM], next_cursor: "page2" })
      .mockResolvedValueOnce({
        items: [{ ...ITEM, id: "123e4567-e89b-12d3-a456-426614174002" }],
        next_cursor: null,
      })
      .mockResolvedValue({ items: [ITEM], next_cursor: "page2" });

    const { result } = renderHook(() => useHomeFeed(vi.fn()));

    await waitFor(() => expect(result.current.status).toBe("ready"));
    act(() => result.current.loadMore());
    await waitFor(() => expect(result.current.items).toHaveLength(2));

    await act(async () => {
      await result.current.refresh();
    });

    expect(feedMock).toHaveBeenCalledTimes(3);
    expect(result.current.items).toHaveLength(1);
  });

  it("reconcile re-reads the loaded range after returning from detail", async () => {
    feedMock
      .mockResolvedValueOnce({ items: [ITEM], next_cursor: "page2" })
      .mockResolvedValueOnce({
        items: [{ ...ITEM, id: "123e4567-e89b-12d3-a456-426614174002" }],
        next_cursor: null,
      });

    const { result } = renderHook(() => useHomeFeed(vi.fn()));

    await waitFor(() => expect(result.current.status).toBe("ready"));
    act(() => result.current.loadMore());
    await waitFor(() => expect(result.current.items).toHaveLength(2));

    feedMock
      .mockResolvedValueOnce({ items: [ITEM], next_cursor: "page2" })
      .mockResolvedValueOnce({
        items: [{ ...ITEM, id: "123e4567-e89b-12d3-a456-426614174002" }],
        next_cursor: null,
      });

    await act(async () => {
      await result.current.reconcile();
    });

    expect(result.current.items).toHaveLength(2);
  });

  it("ignores a pending load-more 401 after the feed becomes inactive", async () => {
    const page = deferred<{ items: FeedItem[]; next_cursor: string | null }>();
    feedMock
      .mockResolvedValueOnce({ items: [ITEM], next_cursor: "page2" })
      .mockReturnValueOnce(page.promise);
    const onSessionLost = vi.fn();

    const { result, rerender } = renderHook(
      ({ active }) => useHomeFeed(onSessionLost, active),
      { initialProps: { active: true } },
    );

    await waitFor(() => expect(result.current.status).toBe("ready"));
    act(() => result.current.loadMore());
    rerender({ active: false });

    await act(async () => {
      page.reject(new ApiError("unauthenticated"));
      await Promise.resolve();
    });

    expect(onSessionLost).not.toHaveBeenCalled();
  });
});

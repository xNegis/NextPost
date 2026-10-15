import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ApiError } from "./api";
import { fetchConsultationDetail, fetchConsultationPhotoUrl, fetchFeed, type FeedItem } from "./consultationApi";
import { useFeedPreviews } from "./useFeedPreviews";
import { useHomeFeed } from "./useHomeFeed";
import { HomeFeed } from "./HomeFeed";
import { PhotoEnlargement } from "./PhotoEnlargement";

vi.mock("./consultationApi", async (importOriginal) => ({
  ...await importOriginal<typeof import("./consultationApi")>(),
  fetchFeed: vi.fn(), fetchConsultationPhotoUrl: vi.fn(), fetchConsultationDetail: vi.fn(),
}));
const photo = vi.mocked(fetchConsultationPhotoUrl);
const feed = vi.mocked(fetchFeed);
let visibility: IntersectionObserverCallback;
class Observer {
  constructor(callback: IntersectionObserverCallback) { visibility = callback; }
  observe() {} unobserve() {} disconnect() {}
}
const item: FeedItem = {
  id: "123e4567-e89b-12d3-a456-426614174000", owner_nickname: "Author",
  question: "Review question", context_excerpt: null, audience: "public", state: "open",
  published_at: "2026-10-15T12:00:00Z", is_owner: false,
  first_photo: { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}
function card(id: string) {
  const element = document.createElement("div");
  element.setAttribute("data-feed-card", id);
  return element;
}
function show(element: HTMLElement) {
  act(() => visibility([{ target: element, isIntersecting: true }] as IntersectionObserverEntry[], {} as IntersectionObserver));
}
beforeEach(() => {
  vi.resetAllMocks(); vi.stubGlobal("IntersectionObserver", Observer);
  feed.mockResolvedValue({ items: [], next_cursor: null });
  vi.mocked(fetchConsultationDetail).mockImplementation(() => new Promise(() => {}));
});
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

it("ignores a preview 401 received after unmount", async () => {
  const request = deferred<string>(); photo.mockReturnValue(request.promise);
  const lost = vi.fn(); const items = [item];
  const { result, unmount } = renderHook(() => useFeedPreviews(items, true, lost));
  const element = card(item.id); act(() => result.current.observe(item.id, element)); show(element);
  await waitFor(() => expect(photo).toHaveBeenCalledTimes(1)); unmount();
  await act(async () => { request.reject(new ApiError("unauthenticated")); await Promise.resolve(); });
  expect(lost).not.toHaveBeenCalled();
});

it("revokes an old preview response after a newer visibility generation", async () => {
  const old = deferred<string>(); const current = deferred<string>();
  photo.mockReturnValueOnce(old.promise).mockReturnValueOnce(current.promise);
  const revoke = vi.spyOn(URL, "revokeObjectURL"); const items = [item]; const lost = vi.fn();
  const { result, rerender } = renderHook(({ active }) => useFeedPreviews(items, active, lost), { initialProps: { active: true } });
  const element = card(item.id); act(() => result.current.observe(item.id, element)); show(element);
  rerender({ active: false }); rerender({ active: true });
  act(() => result.current.observe(item.id, element)); show(element);
  await waitFor(() => expect(photo).toHaveBeenCalledTimes(2));
  await act(async () => { current.resolve("blob:new-review"); });
  await act(async () => { old.resolve("blob:old-review"); });
  expect(result.current.stateFor(item.id)).toEqual({ kind: "ready", url: "blob:new-review" });
  expect(revoke).toHaveBeenCalledWith("blob:old-review");
});

it("loads visible previews with the documented observer fallback", async () => {
  vi.stubGlobal("IntersectionObserver", undefined); photo.mockResolvedValue("blob:fallback");
  const items = [item]; const { result } = renderHook(() => useFeedPreviews(items, true, vi.fn()));
  act(() => result.current.observe(item.id, card(item.id)));
  await waitFor(() => expect(photo).toHaveBeenCalledTimes(1));
});

it("explicit Refresh returns to one newest page after loading more", async () => {
  feed.mockResolvedValueOnce({ items: [item], next_cursor: "page2" })
    .mockResolvedValueOnce({ items: [{ ...item, id: "123e4567-e89b-12d3-a456-426614174002" }], next_cursor: null })
    .mockResolvedValue({ items: [item], next_cursor: "page2" });
  const { result } = renderHook(() => useHomeFeed(vi.fn()));
  await waitFor(() => expect(result.current.status).toBe("ready"));
  act(() => result.current.loadMore()); await waitFor(() => expect(result.current.items).toHaveLength(2));
  await act(async () => { await result.current.refresh(); });
  expect(feed).toHaveBeenCalledTimes(3);
});

it("does not process a hidden Load more 401 while reading detail", async () => {
  const page = deferred<{ items: FeedItem[]; next_cursor: string | null }>();
  feed.mockResolvedValueOnce({ items: [item], next_cursor: "page2" }).mockReturnValueOnce(page.promise);
  const lost = vi.fn(); const user = userEvent.setup(); render(<HomeFeed onSessionLost={lost} />);
  await user.click(await screen.findByRole("button", { name: "Load more" }));
  await user.click(screen.getByRole("button", { name: "View consultation" }));
  expect(screen.getByText("Loading consultation…")).toBeInTheDocument();
  await act(async () => { page.reject(new ApiError("unauthenticated")); await Promise.resolve(); });
  expect(lost).not.toHaveBeenCalled();
});

it("contains keyboard focus inside the photo dialog", async () => {
  const user = userEvent.setup();
  render(<><button>Background action</button><PhotoEnlargement src="blob:review" alt="Review photo" onClose={vi.fn()} /></>);
  const close = screen.getByRole("button", { name: "Close" }); expect(close).toHaveFocus();
  await user.tab(); expect(close).toHaveFocus();
});

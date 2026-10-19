import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  fetchConsultationDetail,
  fetchConsultationPhotoUrl,
  fetchFeed,
  fetchMyConsultation,
  fetchMyVote,
  fetchOwnerLink,
  submitVote,
  type FeedItem,
} from "./consultationApi";
import { HomeFeed } from "./HomeFeed";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchFeed: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
    fetchConsultationDetail: vi.fn(),
    fetchMyConsultation: vi.fn(),
    fetchOwnerLink: vi.fn(),
    fetchMyVote: vi.fn(),
    submitVote: vi.fn(),
  };
});

const feedMock = vi.mocked(fetchFeed);
const photoMock = vi.mocked(fetchConsultationPhotoUrl);
const detailMock = vi.mocked(fetchConsultationDetail);
const ownerDetailMock = vi.mocked(fetchMyConsultation);
const linkMock = vi.mocked(fetchOwnerLink);
const myVoteMock = vi.mocked(fetchMyVote);
const submitVoteMock = vi.mocked(submitVote);

const FEED_ITEM: FeedItem = {
  id: "123e4567-e89b-12d3-a456-426614174000",
  owner_nickname: "Ana",
  question: "Which one?",
  context_excerpt: "Some context",
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

const OWN_ITEM: FeedItem = { ...FEED_ITEM, is_owner: true };

const READER_DETAIL = {
  id: FEED_ITEM.id,
  owner_nickname: "Ana",
  question: "Which one?",
  context: "Full context",
  audience: "public",
  state: "open",
  published_at: "2026-09-28T12:00:00Z",
  photos: [
    { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
  ],
};

const OWNER_DETAIL = {
  id: OWN_ITEM.id,
  state: "open",
  owner_nickname: "Ana",
  question: "Which one?",
  context: null,
  audience: "public",
  published_at: "2026-09-28T12:00:00Z",
  photos: [
    { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
  ],
};

class MockIntersectionObserver {
  callback: IntersectionObserverCallback;
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
  }
  observe(element: Element) {
    this.callback(
      [
        { target: element, isIntersecting: true },
      ] as IntersectionObserverEntry[],
      this as unknown as IntersectionObserver,
    );
  }
  unobserve() {}
  disconnect() {}
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);
  feedMock.mockResolvedValue({ items: [], next_cursor: null });
  photoMock.mockResolvedValue("blob:preview");
  detailMock.mockResolvedValue(READER_DETAIL);
  ownerDetailMock.mockResolvedValue(OWNER_DETAIL);
  linkMock.mockResolvedValue({ active: false, generation: "0", token: null });
  myVoteMock.mockResolvedValue({ status: "not_voted" });
  submitVoteMock.mockResolvedValue({
    status: "voted",
    photo_id: READER_DETAIL.photos[0].id,
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderHome(onSessionLost = vi.fn()) {
  return render(<HomeFeed onSessionLost={onSessionLost} />);
}

describe("HomeFeed", () => {
  it("shows the Home heading and a distinct empty state", async () => {
    renderHome();
    expect(
      await screen.findByRole("heading", { name: "Home" }),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(
        screen.getByText("No open public consultations yet."),
      ).toBeInTheDocument(),
    );
  });

  it("renders cards with question, nickname, facts, Photo 1 and preview", async () => {
    feedMock.mockResolvedValue({ items: [FEED_ITEM], next_cursor: null });
    renderHome();

    expect(await screen.findByText("Which one?")).toBeInTheDocument();
    expect(screen.getByText("Ana")).toBeInTheDocument();
    expect(screen.getByText(/Public · Open · Published/)).toBeInTheDocument();
    expect(screen.getByText("Some context")).toBeInTheDocument();
    expect(screen.getByText("Photo 1")).toBeInTheDocument();
    await waitFor(() =>
      expect(photoMock).toHaveBeenCalledWith(
        FEED_ITEM.id,
        FEED_ITEM.first_photo.id,
      ),
    );
    expect(
      screen.getByRole("button", { name: "View consultation" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Photo 1" }).parentElement,
    ).toHaveStyle({ aspectRatio: "64 / 64" });
  });

  it("marks own cards with Your consultation", async () => {
    feedMock.mockResolvedValue({ items: [OWN_ITEM], next_cursor: null });
    renderHome();
    expect(await screen.findByText("Your consultation")).toBeInTheDocument();
  });

  it("marks an already-voted card with Voted", async () => {
    feedMock.mockResolvedValue({
      items: [{ ...FEED_ITEM, has_voted: true }],
      next_cursor: null,
    });
    renderHome();
    expect(await screen.findByText("Voted")).toBeInTheDocument();
  });

  it("opens the reader detail for another author and returns to Home", async () => {
    feedMock.mockResolvedValue({ items: [FEED_ITEM], next_cursor: null });
    const user = userEvent.setup();
    renderHome();

    await user.click(
      await screen.findByRole("button", { name: "View consultation" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Consultation" }),
    ).toBeInTheDocument();
    expect(detailMock).toHaveBeenCalledWith(FEED_ITEM.id, null);

    await user.click(screen.getByRole("button", { name: "Back to Home" }));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Home" })).toBeInTheDocument(),
    );
  });

  it("focuses the Home heading after Back revalidation removes the card", async () => {
    feedMock
      .mockResolvedValueOnce({ items: [FEED_ITEM], next_cursor: null })
      .mockResolvedValueOnce({ items: [], next_cursor: null });
    const user = userEvent.setup();
    renderHome();

    await user.click(
      await screen.findByRole("button", { name: "View consultation" }),
    );
    await screen.findByRole("heading", { name: "Consultation" });
    await user.click(screen.getByRole("button", { name: "Back to Home" }));

    const heading = await screen.findByRole("heading", { name: "Home" });
    await waitFor(() => expect(heading).toHaveFocus());
  });

  it("opens the owner detail for an own card with Home return", async () => {
    feedMock.mockResolvedValue({ items: [OWN_ITEM], next_cursor: null });
    const user = userEvent.setup();
    renderHome();

    await user.click(
      await screen.findByRole("button", { name: "View consultation" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Your consultation" }),
    ).toBeInTheDocument();
    expect(ownerDetailMock).toHaveBeenCalledWith(OWN_ITEM.id);
    expect(
      screen.getByRole("button", { name: "Back to Home" }),
    ).toBeInTheDocument();
  });

  it("appends the next page on Load more", async () => {
    feedMock
      .mockResolvedValueOnce({ items: [FEED_ITEM], next_cursor: "cursor-1" })
      .mockResolvedValueOnce({
        items: [{ ...FEED_ITEM, id: "123e4567-e89b-12d3-a456-426614174002" }],
        next_cursor: null,
      });
    const user = userEvent.setup();
    renderHome();

    await waitFor(() => expect(feedMock).toHaveBeenCalled());
    await user.click(await screen.findByRole("button", { name: "Load more" }));

    await waitFor(() =>
      expect(screen.getAllByText("Which one?")).toHaveLength(2),
    );
  });

  it("shows a retryable error distinct from empty", async () => {
    feedMock.mockRejectedValue(new Error("offline"));
    renderHome();
    expect(
      await screen.findByText("Could not load consultations."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(
      screen.queryByText("No open public consultations yet."),
    ).not.toBeInTheDocument();
  });

  it("delegates session loss from the feed to the parent", async () => {
    feedMock.mockRejectedValue(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();
    renderHome(onSessionLost);
    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });

  it("shows a generic unavailable placeholder for a denied preview", async () => {
    feedMock.mockResolvedValue({ items: [FEED_ITEM], next_cursor: null });
    photoMock.mockRejectedValue(new ApiError("consultation_unavailable"));
    renderHome();

    expect(
      await screen.findByText("This consultation is unavailable."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Which one?")).not.toBeInTheDocument();
  });
});

import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  fetchConsultationDetail,
  fetchConsultationPhotoUrl,
  fetchMyVote,
  submitVote,
} from "./consultationApi";
import { ReaderConsultationDetail } from "./ReaderConsultationDetail";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchConsultationDetail: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
    fetchMyVote: vi.fn(),
    submitVote: vi.fn(),
  };
});

const detailMock = vi.mocked(fetchConsultationDetail);
const photoMock = vi.mocked(fetchConsultationPhotoUrl);
const myVoteMock = vi.mocked(fetchMyVote);
const submitVoteMock = vi.mocked(submitVote);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";

const DETAIL = {
  id: CONSULTATION_ID,
  owner_nickname: "Ana",
  question: "Which one?",
  context: "For LinkedIn",
  audience: "public",
  state: "open",
  published_at: "2026-09-28T12:00:00Z",
  photos: [
    { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
    { id: "123e4567-e89b-12d3-a456-426614174002", width: 64, height: 64 },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  detailMock.mockResolvedValue(DETAIL);
  photoMock.mockResolvedValue("blob:photo");
  myVoteMock.mockResolvedValue({ status: "not_voted" });
  submitVoteMock.mockResolvedValue({
    status: "voted",
    photo_id: DETAIL.photos[0].id,
  });
});

function renderDetail(onSessionLost = vi.fn()) {
  return render(
    <ReaderConsultationDetail
      consultationId={CONSULTATION_ID}
      onBack={vi.fn()}
      onSessionLost={onSessionLost}
    />,
  );
}

describe("ReaderConsultationDetail", () => {
  it("shows nickname, facts, full text and ordered photos", async () => {
    renderDetail();

    expect(await screen.findByText("Ana")).toBeInTheDocument();
    expect(screen.getByText(/Public · Open · Published/)).toBeInTheDocument();
    expect(screen.getByText("Which one?")).toBeInTheDocument();
    expect(screen.getByText("For LinkedIn")).toBeInTheDocument();

    expect(
      await screen.findByRole("img", { name: "Consultation photo 1" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Photo 1 of 2")).toBeInTheDocument();
    expect(photoMock).toHaveBeenCalledTimes(2);
  });

  it("swipes through one photo at a time and selects the visible choice", async () => {
    const user = userEvent.setup();
    renderDetail();

    await screen.findByText("Photo 1 of 2");
    const track = screen.getByRole("list", {
      name: "Consultation photos. Swipe horizontally to browse.",
    });
    Object.defineProperty(track, "clientWidth", { value: 100 });
    Object.defineProperty(track, "scrollLeft", { value: 100 });
    fireEvent.scroll(track);
    expect(screen.getByText("Photo 2 of 2")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Next photo" }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Choose this photo" }));

    expect(screen.getByRole("button", { name: "Selected" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByText("Photo 2 selected")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review vote" })).toBeEnabled();
  });

  it("settles a partial swipe on the exact photo boundary", async () => {
    vi.useFakeTimers();
    try {
      renderDetail();
      await vi.waitFor(() => {
        expect(screen.getByText("Photo 1 of 2")).toBeInTheDocument();
      });
      const track = screen.getByRole("list", {
        name: "Consultation photos. Swipe horizontally to browse.",
      });
      const scrollTo = vi.fn();
      Object.defineProperty(track, "clientWidth", { value: 100 });
      Object.defineProperty(track, "scrollLeft", { value: 146 });
      Object.defineProperty(track, "scrollTo", { value: scrollTo });

      fireEvent.scroll(track);
      expect(screen.getByText("Photo 2 of 2")).toBeInTheDocument();
      await vi.advanceTimersByTimeAsync(120);

      expect(scrollTo).toHaveBeenCalledWith({ left: 100, behavior: "smooth" });
    } finally {
      vi.useRealTimers();
    }
  });

  it("loads photos in stored order", async () => {
    const urls: string[] = [];
    photoMock.mockImplementation(async (_id, photoId) => {
      const url = `blob:${photoId}`;
      urls.push(photoId);
      return url;
    });
    renderDetail();

    await waitFor(() => expect(urls).toHaveLength(2));
    expect(urls).toEqual([
      "123e4567-e89b-12d3-a456-426614174001",
      "123e4567-e89b-12d3-a456-426614174002",
    ]);
  });

  it("enlarges a photo in an accessible dialog and closes on Escape", async () => {
    const user = userEvent.setup();
    renderDetail();

    await user.click(
      await screen.findByRole("button", { name: "Enlarge photo 1" }),
    );
    const dialog = screen.getByRole("dialog", {
      name: "Full-screen photo gallery",
    });
    expect(dialog).toBeInTheDocument();
    const track = within(dialog).getByRole("list", {
      name: "Full-screen consultation photos. Swipe horizontally to browse.",
    });
    Object.defineProperty(track, "clientWidth", { value: 100 });
    Object.defineProperty(track, "scrollLeft", { value: 100 });
    fireEvent.scroll(track);
    await user.click(
      within(dialog).getByRole("button", { name: "Choose this photo" }),
    );
    expect(
      within(dialog).getByRole("button", { name: "Photo 2 selected" }),
    ).toHaveAttribute("aria-pressed", "true");

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows the generic unavailable message for a denied target", async () => {
    detailMock.mockRejectedValue(new ApiError("consultation_unavailable"));
    renderDetail();

    expect(
      await screen.findByText("This consultation is unavailable."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Back to Home" }),
    ).toBeInTheDocument();
  });

  it("shows a retryable error when a photo fails, without a partial comparison", async () => {
    photoMock.mockRejectedValueOnce(new Error("offline"));
    renderDetail();

    expect(
      await screen.findByText("Could not load this consultation."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("delegates session loss to the parent", async () => {
    detailMock.mockRejectedValue(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();
    renderDetail(onSessionLost);
    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });

  it("selects, reviews, cancels and confirms one immutable vote", async () => {
    const user = userEvent.setup();
    renderDetail();

    await screen.findByText("Choose a photo");
    expect(
      screen.queryByRole("button", { name: "Review vote" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Choose this photo" }));
    await user.click(screen.getByRole("button", { name: "Review vote" }));

    expect(screen.getByText("Review your vote")).toBeInTheDocument();
    expect(
      screen.getByText("Votes are final and cannot be changed."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Selected photo 1" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByText("Review your vote")).not.toBeInTheDocument();
    expect(submitVoteMock).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Review vote" }));
    await user.click(screen.getByRole("button", { name: "Confirm vote" }));

    expect(await screen.findByText("Your vote")).toBeInTheDocument();
    expect(screen.getByText("Votes cannot be changed.")).toBeInTheDocument();
    expect(submitVoteMock).toHaveBeenCalledWith(
      CONSULTATION_ID,
      DETAIL.photos[0].id,
      null,
    );
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
  });

  it("highlights the recorded photo as Your vote when already voted", async () => {
    myVoteMock.mockResolvedValue({
      status: "voted",
      photo_id: DETAIL.photos[1].id,
    });
    renderDetail();

    expect(await screen.findByText("Your vote")).toBeInTheDocument();
    expect(screen.getByText("Votes cannot be changed.")).toBeInTheDocument();
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
  });

  it("offers Check vote status when the status read fails", async () => {
    myVoteMock.mockRejectedValue(new Error("offline"));
    renderDetail();

    expect(
      await screen.findByText("Could not check your vote status."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Check vote status" }),
    ).toBeInTheDocument();
  });

  it("shows unavailable when the vote status read reveals a denial", async () => {
    myVoteMock.mockRejectedValue(new ApiError("consultation_unavailable"));
    renderDetail();

    expect(
      await screen.findByText("This consultation is unavailable."),
    ).toBeInTheDocument();
  });

  it("refreshes both protected detail and vote status after a denial", async () => {
    myVoteMock
      .mockRejectedValueOnce(new ApiError("consultation_unavailable"))
      .mockResolvedValueOnce({ status: "not_voted" });
    const user = userEvent.setup();
    renderDetail();

    await screen.findByText("This consultation is unavailable.");
    await user.click(screen.getByRole("button", { name: "Refresh" }));

    expect(await screen.findByText("Choose a photo")).toBeInTheDocument();
    expect(detailMock).toHaveBeenCalledTimes(2);
    expect(myVoteMock).toHaveBeenCalledTimes(2);
  });

  it("delegates session loss from the vote status read", async () => {
    myVoteMock.mockRejectedValue(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();
    renderDetail(onSessionLost);
    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  fetchConsultationDetail,
  fetchConsultationEntry,
  fetchConsultationPhotoUrl,
  fetchMyConsultation,
  fetchMyConsultationResults,
  fetchMyVote,
  fetchOwnerLink,
} from "./consultationApi";
import type { ConsultationDestination } from "./consultationLink";
import { DirectConsultationEntry } from "./DirectConsultationEntry";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchConsultationEntry: vi.fn(),
    fetchConsultationDetail: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
    fetchMyVote: vi.fn(),
    fetchMyConsultation: vi.fn(),
    fetchOwnerLink: vi.fn(),
    fetchMyConsultationResults: vi.fn(),
  };
});

const entryMock = vi.mocked(fetchConsultationEntry);
const detailMock = vi.mocked(fetchConsultationDetail);
const photoMock = vi.mocked(fetchConsultationPhotoUrl);
const myVoteMock = vi.mocked(fetchMyVote);
const ownerDetailMock = vi.mocked(fetchMyConsultation);
const ownerLinkMock = vi.mocked(fetchOwnerLink);
const resultsMock = vi.mocked(fetchMyConsultationResults);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";
const TOKEN = `v1.${"A".repeat(43)}`;

const DESTINATION: ConsultationDestination = {
  consultationId: CONSULTATION_ID,
  token: null,
};

const readerDetail = {
  id: CONSULTATION_ID,
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

const ownerDetail = {
  id: CONSULTATION_ID,
  state: "open" as const,
  owner_nickname: "Ana",
  question: "Which one?",
  context: null,
  audience: "public" as const,
  published_at: "2026-09-28T12:00:00Z",
  photos: [{ id: "photo-1", width: 100, height: 200 }],
};

beforeEach(() => {
  vi.clearAllMocks();
  photoMock.mockResolvedValue("blob:photo");
  myVoteMock.mockResolvedValue({ status: "not_voted" });
  ownerLinkMock.mockResolvedValue({
    active: true,
    generation: "1",
    token: TOKEN,
  });
  resultsMock.mockResolvedValue({
    consultation_id: CONSULTATION_ID,
    state: "open",
    total_votes: 0,
    options: [{ photo_id: "photo-1", ordinal: 0, vote_count: 0 }],
  });
});

function renderEntry(
  destination: ConsultationDestination = DESTINATION,
  onSessionLost = vi.fn(),
) {
  return render(
    <DirectConsultationEntry
      destination={destination}
      onGoHome={vi.fn()}
      onSessionLost={onSessionLost}
    />,
  );
}

describe("DirectConsultationEntry", () => {
  it("renders neutral owner detail with Go to Home for an owner role", async () => {
    entryMock.mockResolvedValue({ role: "owner" });
    ownerDetailMock.mockResolvedValue(ownerDetail);

    renderEntry();

    expect(
      await screen.findByRole("heading", { name: "Your consultation" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Go to Home" }),
    ).toBeInTheDocument();
  });

  it("renders the real reader flow with Go to Home for a reader role", async () => {
    entryMock.mockResolvedValue({ role: "reader" });
    detailMock.mockResolvedValue(readerDetail);

    renderEntry();

    expect(await screen.findByText("Ana")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to Home" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Back to Home" }),
    ).not.toBeInTheDocument();
  });

  it("passes the parsed private token to the reader detail", async () => {
    entryMock.mockResolvedValue({ role: "reader" });
    detailMock.mockResolvedValue(readerDetail);

    renderEntry({ consultationId: CONSULTATION_ID, token: TOKEN });

    await waitFor(() =>
      expect(detailMock).toHaveBeenCalledWith(CONSULTATION_ID, TOKEN),
    );
  });

  it("shows a generic unavailable result for a denied target", async () => {
    entryMock.mockRejectedValue(new ApiError("consultation_unavailable"));

    renderEntry();

    expect(
      await screen.findByText("This consultation is unavailable."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to Home" }),
    ).toBeInTheDocument();
  });

  it("shows a retryable error and recovers on retry", async () => {
    const user = userEvent.setup();
    entryMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ role: "owner" });
    ownerDetailMock.mockResolvedValue(ownerDetail);

    renderEntry();

    expect(
      await screen.findByText("Could not load this consultation."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(
      await screen.findByRole("heading", { name: "Your consultation" }),
    ).toBeInTheDocument();
    expect(entryMock).toHaveBeenCalledTimes(2);
  });

  it("delegates session loss on an unauthenticated entry read", async () => {
    const onSessionLost = vi.fn();
    entryMock.mockRejectedValue(new ApiError("unauthenticated"));

    renderEntry(DESTINATION, onSessionLost);

    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });
});

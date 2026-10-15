import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  fetchConsultationDetail,
  fetchConsultationPhotoUrl,
} from "./consultationApi";
import { ReaderConsultationDetail } from "./ReaderConsultationDetail";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchConsultationDetail: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
  };
});

const detailMock = vi.mocked(fetchConsultationDetail);
const photoMock = vi.mocked(fetchConsultationPhotoUrl);

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

    await waitFor(() =>
      expect(
        screen.getAllByRole("img", { name: /Consultation photo/ }),
      ).toHaveLength(2),
    );
    expect(photoMock).toHaveBeenCalledTimes(2);
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
    expect(screen.getByRole("dialog")).toBeInTheDocument();

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
});

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  createOwnerLink,
  deleteConsultation,
  disableOwnerLink,
  fetchConsultationPhotoUrl,
  fetchMyConsultation,
  fetchOwnerLink,
  replaceOwnerLink,
} from "./consultationApi";
import { PublishedSuccess } from "./PublishedSuccess";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchMyConsultation: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
    fetchOwnerLink: vi.fn(),
    disableOwnerLink: vi.fn(),
    replaceOwnerLink: vi.fn(),
    createOwnerLink: vi.fn(),
    deleteConsultation: vi.fn(),
  };
});

const fetchDetailMock = vi.mocked(fetchMyConsultation);
const fetchPhotoUrlMock = vi.mocked(fetchConsultationPhotoUrl);
const fetchOwnerLinkMock = vi.mocked(fetchOwnerLink);
const disableOwnerLinkMock = vi.mocked(disableOwnerLink);
const replaceOwnerLinkMock = vi.mocked(replaceOwnerLink);
const createOwnerLinkMock = vi.mocked(createOwnerLink);
const deleteMock = vi.mocked(deleteConsultation);

const openDetail = {
  id: "123e4567-e89b-12d3-a456-426614174000",
  owner_nickname: "Ana",
  question: "Which one?",
  context: null,
  audience: "public" as const,
  state: "open" as const,
  published_at: "2026-09-28T12:00:00Z",
  photos: [
    { id: "photo-1", width: 100, height: 200 },
    { id: "photo-2", width: 150, height: 100 },
  ],
};

const ACTIVE_TOKEN = `v1.${"a".repeat(43)}`;
const REPLACED_TOKEN = `v1.${"b".repeat(43)}`;

beforeEach(() => {
  vi.clearAllMocks();
  fetchDetailMock.mockResolvedValue(openDetail);
  fetchPhotoUrlMock.mockResolvedValue("blob:photo");
  fetchOwnerLinkMock.mockResolvedValue({
    active: true,
    generation: "1",
    token: ACTIVE_TOKEN,
  });
  disableOwnerLinkMock.mockResolvedValue({
    active: false,
    generation: "1",
    token: null,
  });
  replaceOwnerLinkMock.mockResolvedValue({
    active: true,
    generation: "2",
    token: REPLACED_TOKEN,
  });
  createOwnerLinkMock.mockResolvedValue({
    active: true,
    generation: "2",
    token: REPLACED_TOKEN,
  });
  deleteMock.mockResolvedValue(undefined);
});

function renderSuccess(
  props: Partial<Parameters<typeof PublishedSuccess>[0]> = {},
) {
  return render(
    <PublishedSuccess
      consultationId="123e4567-e89b-12d3-a456-426614174000"
      onBack={vi.fn()}
      onSessionLost={vi.fn()}
      {...props}
    />,
  );
}

describe("PublishedSuccess", () => {
  it("shows loading state", () => {
    renderSuccess();
    expect(screen.getByText("Loading your consultation…")).toBeInTheDocument();
  });

  it("shows published detail after loading", async () => {
    renderSuccess();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    expect(
      screen.getByText("Your consultation is now live."),
    ).toBeInTheDocument();
  });

  it("shows the Open status after the persisted detail loads", async () => {
    renderSuccess();
    await waitFor(() => expect(screen.getByText("Open")).toBeInTheDocument());
  });

  it("shows published photos", async () => {
    renderSuccess();
    await waitFor(() =>
      expect(
        screen.getByRole("img", { name: "Consultation photo 1" }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("img", { name: "Consultation photo 2" }),
    ).toBeInTheDocument();
  });

  it("shows error state with retry and back", async () => {
    fetchDetailMock.mockRejectedValue(new Error("offline"));
    const user = userEvent.setup();
    const onBack = vi.fn();

    renderSuccess({ onBack });

    await waitFor(() =>
      expect(
        screen.getByText("Could not load your consultation."),
      ).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Back Home" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("does not show private link for public consultations", async () => {
    renderSuccess();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Private link")).not.toBeInTheDocument();
    expect(fetchOwnerLinkMock).not.toHaveBeenCalled();
  });

  it("shows private link controls for private consultations", async () => {
    fetchDetailMock.mockResolvedValue({ ...openDetail, audience: "private" });
    renderSuccess();
    await waitFor(() =>
      expect(screen.getByText("Private link")).toBeInTheDocument(),
    );
    expect(screen.getByText("Current link")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Copy link" }),
    ).toBeInTheDocument();
  });

  it("offers a View in My consultations action for published consultations", async () => {
    const onViewInMyConsultations = vi.fn();
    const user = userEvent.setup();
    renderSuccess({ onViewInMyConsultations });
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    await user.click(
      screen.getByRole("button", { name: "View in My consultations" }),
    );
    expect(onViewInMyConsultations).toHaveBeenCalledTimes(1);
  });

  it("handles session lost on detail load", async () => {
    fetchDetailMock.mockRejectedValue(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();

    renderSuccess({ onSessionLost });

    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });

  it("reports deletion of a freshly published consultation through onDeleted", async () => {
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    renderSuccess({ onDeleted });
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    await user.click(
      within(
        screen.getByRole("dialog", { name: "Delete consultation?" }),
      ).getByRole("button", { name: "Delete consultation" }),
    );

    await waitFor(() => expect(onDeleted).toHaveBeenCalledWith("open"));
    expect(deleteMock).toHaveBeenCalledWith(
      "123e4567-e89b-12d3-a456-426614174000",
      "open",
    );
  });

  it("disables a private link", async () => {
    fetchDetailMock.mockResolvedValue({ ...openDetail, audience: "private" });
    const user = userEvent.setup();
    renderSuccess();
    await waitFor(() =>
      expect(screen.getByText("Private link")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: "Disable link" }));
    await user.click(screen.getByRole("button", { name: "Disable link" }));
    await waitFor(() => expect(disableOwnerLinkMock).toHaveBeenCalledTimes(1));
    expect(disableOwnerLinkMock).toHaveBeenCalledWith(
      "123e4567-e89b-12d3-a456-426614174000",
      "1",
    );
  });

  it("replaces a private link", async () => {
    fetchDetailMock.mockResolvedValue({ ...openDetail, audience: "private" });
    const user = userEvent.setup();
    renderSuccess();
    await waitFor(() =>
      expect(screen.getByText("Private link")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: "Replace link" }));
    await user.click(screen.getByRole("button", { name: "Replace link" }));
    await waitFor(() => expect(replaceOwnerLinkMock).toHaveBeenCalledTimes(1));
  });
});

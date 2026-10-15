import {
  act,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  disableOwnerLink,
  fetchConsultationPhotoUrl,
  fetchMyConsultation,
  fetchOwnerLink,
} from "./consultationApi";
import { OwnerConsultationDetail } from "./OwnerConsultationDetail";
import { useOwnerConsultationDetail } from "./useOwnerConsultationDetail";

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
  };
});

const fetchDetailMock = vi.mocked(fetchMyConsultation);
const fetchPhotoUrlMock = vi.mocked(fetchConsultationPhotoUrl);
const fetchOwnerLinkMock = vi.mocked(fetchOwnerLink);
const disableOwnerLinkMock = vi.mocked(disableOwnerLink);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";

const openDetail = {
  id: CONSULTATION_ID,
  state: "open" as const,
  owner_nickname: "Ana",
  question: "Which one?",
  context: null,
  audience: "public" as const,
  published_at: "2026-09-28T12:00:00Z",
  photos: [{ id: "photo-1", width: 100, height: 200 }],
};

const finalizedDetail = {
  id: CONSULTATION_ID,
  state: "finalized" as const,
  published_at: "2026-09-28T12:00:00Z",
};

const ACTIVE_TOKEN = `v1.${"a".repeat(43)}`;

beforeEach(() => {
  vi.clearAllMocks();
  fetchDetailMock.mockResolvedValue(openDetail);
  fetchPhotoUrlMock.mockResolvedValue("blob:photo");
  fetchOwnerLinkMock.mockResolvedValue({
    active: true,
    generation: "1",
    token: ACTIVE_TOKEN,
  });
});

function renderReturning() {
  return render(
    <OwnerConsultationDetail
      consultationId={CONSULTATION_ID}
      variant="returning"
      onBack={vi.fn()}
      onSessionLost={vi.fn()}
    />,
  );
}

describe("OwnerConsultationDetail", () => {
  it("releases partial URLs immediately on unmount and ignores the late 401", async () => {
    const revoke = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => {});
    let rejectPhoto!: (error: unknown) => void;
    const pending = new Promise<string>((_, reject) => {
      rejectPhoto = reject;
    });
    fetchDetailMock.mockResolvedValue({
      ...openDetail,
      photos: [
        { id: "photo-1", width: 100, height: 200 },
        { id: "photo-2", width: 100, height: 200 },
      ],
    });
    fetchPhotoUrlMock
      .mockResolvedValueOnce("blob:partial")
      .mockReturnValueOnce(pending);
    const onSessionLost = vi.fn();
    const view = renderHook(() =>
      useOwnerConsultationDetail(CONSULTATION_ID, onSessionLost),
    );
    await waitFor(() => expect(fetchPhotoUrlMock).toHaveBeenCalledTimes(2));
    view.unmount();
    expect(revoke).toHaveBeenCalledWith("blob:partial");
    await act(async () => {
      rejectPhoto(new ApiError("unauthenticated"));
    });
    expect(onSessionLost).not.toHaveBeenCalled();
    expect(revoke).toHaveBeenCalledTimes(1);
    revoke.mockRestore();
  });

  it("revokes a photo that finishes after the detail has unmounted", async () => {
    const revoke = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => {});
    let resolvePhoto!: (url: string) => void;
    fetchPhotoUrlMock.mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePhoto = resolve;
      }),
    );
    const view = renderHook(() =>
      useOwnerConsultationDetail(CONSULTATION_ID, vi.fn()),
    );
    await waitFor(() => expect(fetchPhotoUrlMock).toHaveBeenCalledTimes(1));
    view.unmount();
    await act(async () => {
      resolvePhoto("blob:late");
    });
    expect(revoke).toHaveBeenCalledWith("blob:late");
    revoke.mockRestore();
  });

  it("loads the next item without letting the previous Private detail cancel it", async () => {
    fetchDetailMock.mockResolvedValueOnce({
      ...openDetail,
      audience: "private",
    });
    const onSessionLost = vi.fn();
    const view = renderHook(
      ({ id }) => useOwnerConsultationDetail(id, onSessionLost),
      {
        initialProps: { id: CONSULTATION_ID },
      },
    );
    await waitFor(() => expect(view.result.current.link.kind).toBe("ready"));
    const nextId = "123e4567-e89b-12d3-a456-426614174001";
    fetchDetailMock.mockResolvedValueOnce({ ...openDetail, id: nextId });
    view.rerender({ id: nextId });
    await waitFor(() => expect(view.result.current.phase.kind).toBe("open"));
    expect(view.result.current.phase).toMatchObject({ detail: { id: nextId } });
    expect(fetchOwnerLinkMock).toHaveBeenCalledTimes(1);
  });

  it("uses neutral wording when returning to an existing consultation", async () => {
    renderReturning();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("heading", { name: "Your consultation" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Your consultation is now live."),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Back to My consultations" }),
    ).toBeInTheDocument();
  });

  it("shows the published date and audience reach", async () => {
    renderReturning();
    await waitFor(() => expect(screen.getByText("Open")).toBeInTheDocument());
    expect(screen.getByText("Published", { exact: false })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Public: anyone with an account can find and see this consultation.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the minimum finalized summary with no photos or link", async () => {
    fetchDetailMock.mockResolvedValue(finalizedDetail);
    renderReturning();
    await waitFor(() =>
      expect(
        screen.getByText("Photos are no longer available."),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText(CONSULTATION_ID)).toBeInTheDocument();
    expect(screen.getByText("Finalized")).toBeInTheDocument();
    expect(fetchOwnerLinkMock).not.toHaveBeenCalled();
    expect(fetchPhotoUrlMock).not.toHaveBeenCalled();
  });

  it("shows a generic unavailable view for unknown or non-owner targets", async () => {
    fetchDetailMock.mockRejectedValue(new ApiError("consultation_unavailable"));
    renderReturning();
    await waitFor(() =>
      expect(
        screen.getByText("This consultation is unavailable."),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Back to My consultations" }),
    ).toBeInTheDocument();
  });

  it("reconciles an unavailable photo to the finalized summary", async () => {
    fetchDetailMock
      .mockResolvedValueOnce(openDetail)
      .mockResolvedValueOnce(finalizedDetail);
    fetchPhotoUrlMock.mockRejectedValue(
      new ApiError("consultation_unavailable"),
    );

    renderReturning();

    await waitFor(() =>
      expect(
        screen.getByText("Photos are no longer available."),
      ).toBeInTheDocument(),
    );
    expect(fetchDetailMock).toHaveBeenCalledTimes(2);
  });

  it("releases object URLs when a later photo load fails", async () => {
    const revokeSpy = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => {});
    fetchDetailMock.mockResolvedValue({
      ...openDetail,
      photos: [
        { id: "photo-1", width: 100, height: 200 },
        { id: "photo-2", width: 100, height: 200 },
      ],
    });
    fetchPhotoUrlMock
      .mockResolvedValueOnce("blob:1")
      .mockRejectedValueOnce(new ApiError("network"));

    renderReturning();

    await waitFor(() =>
      expect(
        screen.getByText("Could not load your consultation."),
      ).toBeInTheDocument(),
    );
    expect(revokeSpy).toHaveBeenCalledWith("blob:1");
    revokeSpy.mockRestore();
  });

  it("requires a refresh after an uncertain link mutation", async () => {
    fetchDetailMock.mockResolvedValue({ ...openDetail, audience: "private" });
    disableOwnerLinkMock.mockRejectedValue(new ApiError("link_conflict"));
    const user = userEvent.setup();

    renderReturning();

    await waitFor(() =>
      expect(screen.getByText("Private link")).toBeInTheDocument(),
    );
    await user.click(screen.getByRole("button", { name: "Disable link" }));
    await user.click(screen.getByRole("button", { name: "Disable link" }));

    await waitFor(() =>
      expect(
        screen.getByText("The link changed. Refresh before trying again."),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Refresh link" }),
    ).toBeInTheDocument();
  });

  it("revokes already-loaded photo URLs when a later photo load hits 401", async () => {
    const revokeSpy = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => {});
    fetchDetailMock.mockResolvedValue({
      ...openDetail,
      photos: [
        { id: "photo-1", width: 100, height: 200 },
        { id: "photo-2", width: 100, height: 200 },
      ],
    });
    fetchPhotoUrlMock
      .mockResolvedValueOnce("blob:1")
      .mockRejectedValueOnce(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();

    render(
      <OwnerConsultationDetail
        consultationId={CONSULTATION_ID}
        variant="returning"
        onBack={vi.fn()}
        onSessionLost={onSessionLost}
      />,
    );

    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
    expect(revokeSpy).toHaveBeenCalledWith("blob:1");
    revokeSpy.mockRestore();
  });

  it("clears protected content immediately when a denied read reconciles", async () => {
    let resolveReconcile: (value: unknown) => void = () => undefined;
    const reconcilePromise = new Promise((resolve) => {
      resolveReconcile = resolve;
    });
    fetchDetailMock
      .mockResolvedValueOnce({ ...openDetail, audience: "private" })
      .mockResolvedValueOnce(reconcilePromise);
    fetchPhotoUrlMock.mockResolvedValue("blob:photo");
    fetchOwnerLinkMock.mockRejectedValue(
      new ApiError("consultation_unavailable"),
    );

    renderReturning();

    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    await waitFor(() =>
      expect(
        screen.getByText("Loading your consultation…"),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("Which one?")).not.toBeInTheDocument();

    resolveReconcile(finalizedDetail);
    await waitFor(() =>
      expect(
        screen.getByText("Photos are no longer available."),
      ).toBeInTheDocument(),
    );
  });

  it("offers Refresh on the loaded open detail", async () => {
    const user = userEvent.setup();
    renderReturning();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: "Refresh" }));

    await waitFor(() => expect(fetchDetailMock).toHaveBeenCalledTimes(2));
  });

  it("delegates session loss on the owner read", async () => {
    fetchDetailMock.mockRejectedValue(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();
    render(
      <OwnerConsultationDetail
        consultationId={CONSULTATION_ID}
        variant="returning"
        onBack={vi.fn()}
        onSessionLost={onSessionLost}
      />,
    );
    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });
});

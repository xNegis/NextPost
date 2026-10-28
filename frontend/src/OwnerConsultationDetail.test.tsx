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
  deleteConsultation,
  disableOwnerLink,
  fetchConsultationPhotoUrl,
  fetchMyConsultation,
  fetchMyConsultationResults,
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
    fetchMyConsultationResults: vi.fn(),
    disableOwnerLink: vi.fn(),
    replaceOwnerLink: vi.fn(),
    createOwnerLink: vi.fn(),
    deleteConsultation: vi.fn(),
  };
});

const fetchDetailMock = vi.mocked(fetchMyConsultation);
const fetchPhotoUrlMock = vi.mocked(fetchConsultationPhotoUrl);
const fetchOwnerLinkMock = vi.mocked(fetchOwnerLink);
const fetchResultsMock = vi.mocked(fetchMyConsultationResults);
const disableOwnerLinkMock = vi.mocked(disableOwnerLink);
const deleteConsultationMock = vi.mocked(deleteConsultation);

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
  result: null,
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
  fetchResultsMock.mockResolvedValue({
    consultation_id: CONSULTATION_ID,
    state: "open",
    total_votes: 0,
    options: [{ photo_id: "photo-1", ordinal: 0, vote_count: 0 }],
  });
  deleteConsultationMock.mockResolvedValue(undefined);
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

function renderVariant(variant: "success" | "returning" | "home" | "direct") {
  return render(
    <OwnerConsultationDetail
      consultationId={CONSULTATION_ID}
      variant={variant}
      onBack={vi.fn()}
      onSessionLost={vi.fn()}
    />,
  );
}

describe("OwnerConsultationDetail", () => {
  it.each(["success", "returning", "home", "direct"] as const)(
    "offers the token-free Public URL in the %s owner context",
    async (variant) => {
      renderVariant(variant);

      expect(
        await screen.findByRole("heading", { name: "Share consultation" }),
      ).toBeInTheDocument();
      expect(screen.getByLabelText("Consultation link")).toHaveValue(
        `${window.location.origin}/consultations/${CONSULTATION_ID}`,
      );
      expect(screen.getByRole("button", { name: "Copy link" })).toBeEnabled();
    },
  );

  it("offers only the current active Private fragment URL", async () => {
    fetchDetailMock.mockResolvedValue({ ...openDetail, audience: "private" });
    renderReturning();

    expect(await screen.findByLabelText("Consultation link")).toHaveValue(
      `${window.location.origin}/consultations/${CONSULTATION_ID}#access=${ACTIVE_TOKEN}`,
    );
    expect(fetchOwnerLinkMock).toHaveBeenCalledWith(CONSULTATION_ID);
  });

  it("exposes no shareable URL while the Private link is disabled", async () => {
    fetchDetailMock.mockResolvedValue({ ...openDetail, audience: "private" });
    fetchOwnerLinkMock.mockResolvedValue({
      active: false,
      generation: "2",
      token: null,
    });
    renderReturning();

    expect(
      await screen.findByText("Share is unavailable right now."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Copy link" }),
    ).not.toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Create new link" }),
    ).toBeEnabled();
  });

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
    expect(fetchResultsMock).not.toHaveBeenCalled();
  });

  it("renders the finalized result summary", async () => {
    fetchDetailMock.mockResolvedValue({
      ...finalizedDetail,
      result: {
        finalized_at: "2026-09-28T12:05:00Z",
        total_votes: 3,
        declaration: "selected",
        selected_ordinals: [0],
        options: [
          { ordinal: 0, vote_count: 2, selected: true },
          { ordinal: 1, vote_count: 1, selected: false },
        ],
      },
    });
    renderReturning();
    await waitFor(() =>
      expect(screen.getByText("Final result")).toBeInTheDocument(),
    );
    expect(screen.getByText("3 votes")).toBeInTheDocument();
    expect(screen.getByText("Photo 1")).toBeInTheDocument();
    expect(screen.getByText("Photo 2 · 1 vote")).toBeInTheDocument();
  });

  it("offers Finalize on an open owned detail", async () => {
    renderReturning();
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Finalize consultation" }),
      ).toBeInTheDocument(),
    );
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

  it("shows the total and per-photo counts for an open consultation", async () => {
    fetchResultsMock.mockResolvedValue({
      consultation_id: CONSULTATION_ID,
      state: "open",
      total_votes: 1,
      options: [{ photo_id: "photo-1", ordinal: 0, vote_count: 1 }],
    });
    renderReturning();
    await waitFor(() => expect(screen.getAllByText("1 vote")).toHaveLength(2));
    expect(screen.getByText("Photo 1 of 1")).toBeInTheDocument();
    expect(
      screen.getByText(
        "These are participant opinions and may change while your consultation is open.",
      ),
    ).toBeInTheDocument();
  });

  it("shows a retryable error when results fail to load", async () => {
    fetchResultsMock.mockRejectedValue(new Error("offline"));
    renderReturning();
    await waitFor(() =>
      expect(screen.getByText("Could not load results.")).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("shows a distinct unavailable-results state without stale counts", async () => {
    fetchResultsMock.mockRejectedValue(
      new ApiError("consultation_unavailable"),
    );
    renderReturning();
    await waitFor(() =>
      expect(
        screen.getByText(
          "Results are unavailable. Refresh the consultation to check its current state.",
        ),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("0 votes")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Refresh consultation" }),
    ).toBeInTheDocument();
  });

  it("does not restart photo loads when results refresh", async () => {
    vi.useFakeTimers();
    try {
      renderReturning();
      await act(async () => {
        await vi.advanceTimersByTimeAsync(0);
      });
      expect(fetchPhotoUrlMock).toHaveBeenCalledTimes(1);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(5000);
      });
      expect(fetchResultsMock).toHaveBeenCalledTimes(2);
      expect(fetchPhotoUrlMock).toHaveBeenCalledTimes(1);
      expect(fetchDetailMock).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it("offers deletion on an open owned detail", async () => {
    renderReturning();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Delete consultation" }),
    ).toBeInTheDocument();
  });

  it("offers deletion on a finalized owned detail", async () => {
    fetchDetailMock.mockResolvedValue(finalizedDetail);
    renderReturning();
    await waitFor(() =>
      expect(
        screen.getByText("Photos are no longer available."),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Delete consultation" }),
    ).toBeInTheDocument();
  });

  it("opens the accessible confirmation dialog from an open detail", async () => {
    const user = userEvent.setup();
    renderReturning();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    expect(
      screen.getByRole("dialog", { name: "Delete consultation?" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Access ends immediately\. Every photograph is permanently scheduled for deletion/,
      ),
    ).toBeInTheDocument();
  });
});

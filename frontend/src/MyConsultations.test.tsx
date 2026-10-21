import {
  act,
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
  deleteConsultation,
  fetchConsultationPhotoUrl,
  fetchMyConsultation,
  fetchMyConsultations,
  fetchOwnerLink,
  finalizeConsultation,
} from "./consultationApi";
import { MyConsultations } from "./MyConsultations";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchMyConsultations: vi.fn(),
    fetchMyConsultation: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
    fetchOwnerLink: vi.fn(),
    disableOwnerLink: vi.fn(),
    replaceOwnerLink: vi.fn(),
    createOwnerLink: vi.fn(),
    deleteConsultation: vi.fn(),
    finalizeConsultation: vi.fn(),
  };
});

const listMock = vi.mocked(fetchMyConsultations);
const detailMock = vi.mocked(fetchMyConsultation);
const photoMock = vi.mocked(fetchConsultationPhotoUrl);
const linkMock = vi.mocked(fetchOwnerLink);
const finalizeMock = vi.mocked(finalizeConsultation);
const deleteMock = vi.mocked(deleteConsultation);

const OPEN_ITEM = {
  id: "123e4567-e89b-12d3-a456-426614174000",
  state: "open" as const,
  question: "Which one?",
  audience: "public" as const,
  published_at: "2026-09-28T12:00:00Z",
  total_votes: 3,
};

const FINALIZED_ITEM = {
  id: "123e4567-e89b-12d3-a456-426614174001",
  state: "finalized" as const,
  published_at: "2026-09-28T12:00:00Z",
  result: null,
};

const OPEN_DETAIL = {
  id: OPEN_ITEM.id,
  state: "open" as const,
  owner_nickname: "Ana",
  question: "Which one?",
  context: null,
  audience: "public" as const,
  published_at: "2026-09-28T12:00:00Z",
  photos: [{ id: "photo-1", width: 100, height: 200 }],
};

const FINALIZED_DETAIL = {
  id: OPEN_ITEM.id,
  state: "finalized" as const,
  published_at: "2026-09-28T12:00:00Z",
  result: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  listMock.mockResolvedValue({ items: [], next_cursor: null });
  detailMock.mockResolvedValue(OPEN_DETAIL);
  photoMock.mockResolvedValue("blob:photo");
  linkMock.mockResolvedValue({ active: true, generation: "1", token: null });
  deleteMock.mockResolvedValue(undefined);
  finalizeMock.mockResolvedValue({
    id: OPEN_ITEM.id,
    state: "finalized",
    published_at: "2026-09-28T12:00:00Z",
    result: null,
  });
});

function renderList(
  props: Partial<Parameters<typeof MyConsultations>[0]> = {},
) {
  return render(
    <MyConsultations
      selectedId={null}
      onSelectionChange={vi.fn()}
      onSessionLost={vi.fn()}
      onCreate={vi.fn()}
      {...props}
    />,
  );
}

describe("MyConsultations", () => {
  it("loads the list on Back when direct detail entry invalidated the initial request", async () => {
    listMock.mockReturnValueOnce(new Promise(() => {}));
    const onSelectionChange = vi.fn();
    const view = renderList({ selectedId: OPEN_ITEM.id, onSelectionChange });
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Back to My consultations" }));
    expect(onSelectionChange).toHaveBeenCalledWith(null);
    view.rerender(
      <MyConsultations
        selectedId={null}
        onSelectionChange={onSelectionChange}
        onSessionLost={vi.fn()}
        onCreate={vi.fn()}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("You have no open consultations."),
      ).toBeInTheDocument(),
    );
    expect(listMock).toHaveBeenCalledTimes(2);
  });

  it("returns to the list, announces and refetches after deletion", async () => {
    const onSelectionChange = vi.fn();
    const view = renderList({ selectedId: OPEN_ITEM.id, onSelectionChange });
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    const user = userEvent.setup();
    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    const dialog = screen.getByRole("dialog", {
      name: "Delete consultation?",
    });
    await user.click(
      within(dialog).getByRole("button", { name: "Delete consultation" }),
    );

    await waitFor(() =>
      expect(deleteMock).toHaveBeenCalledWith(OPEN_ITEM.id, "open"),
    );
    expect(onSelectionChange).toHaveBeenCalledWith(null);

    view.rerender(
      <MyConsultations
        selectedId={null}
        onSelectionChange={onSelectionChange}
        onSessionLost={vi.fn()}
        onCreate={vi.fn()}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText("Consultation deleted")).toBeInTheDocument(),
    );
    expect(listMock).toHaveBeenCalled();
  });

  it("shows heading and Open/Finalized tabs with Open selected", async () => {
    renderList();
    expect(
      screen.getByRole("heading", { name: "My consultations" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Open" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: "Finalized" })).toHaveAttribute(
      "aria-selected",
      "false",
    );
    await waitFor(() => expect(listMock).toHaveBeenCalled());
  });

  it("shows a distinct empty open state with a create action", async () => {
    const onCreate = vi.fn();
    const user = userEvent.setup();
    renderList({ onCreate });
    await waitFor(() =>
      expect(
        screen.getByText("You have no open consultations."),
      ).toBeInTheDocument(),
    );
    await user.click(
      screen.getByRole("button", { name: "Create consultation" }),
    );
    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it("shows the finalized empty state when switching tabs", async () => {
    const user = userEvent.setup();
    renderList();
    await user.click(screen.getByRole("tab", { name: "Finalized" }));
    await waitFor(() =>
      expect(
        screen.getByText("You have no finalized consultations."),
      ).toBeInTheDocument(),
    );
    expect(listMock).toHaveBeenLastCalledWith("finalized", 20, null);
  });

  it("renders open rows with question, audience, state and date", async () => {
    listMock.mockResolvedValue({ items: [OPEN_ITEM], next_cursor: null });
    renderList();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    expect(screen.getByText(/Public · Open · Published/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "View consultation" }),
    ).toBeInTheDocument();
  });

  it("renders finalized rows with reference and state", async () => {
    const user = userEvent.setup();
    listMock.mockResolvedValue({ items: [FINALIZED_ITEM], next_cursor: null });
    renderList();
    await user.click(screen.getByRole("tab", { name: "Finalized" }));
    await waitFor(() =>
      expect(
        screen.getByText(`Consultation ${FINALIZED_ITEM.id}`),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText(/Finalized · Published/)).toBeInTheDocument();
  });

  it("renders the finalized result in list rows", async () => {
    const user = userEvent.setup();
    listMock.mockResolvedValue({
      items: [
        {
          ...FINALIZED_ITEM,
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
        },
      ],
      next_cursor: null,
    });
    const { container } = renderList();
    await user.click(screen.getByRole("tab", { name: "Finalized" }));
    await waitFor(() =>
      expect(screen.getByText("Photo 1 · 3 votes")).toBeInTheDocument(),
    );
    expect(
      container.querySelector('time[datetime="2026-09-28T12:05:00Z"]'),
    ).toBeInTheDocument();
  });

  it("keeps the detail open and refetches the finalized detail after finalizing", async () => {
    const user = userEvent.setup();
    const onSelectionChange = vi.fn();
    detailMock
      .mockResolvedValueOnce(OPEN_DETAIL)
      .mockResolvedValueOnce(FINALIZED_DETAIL);
    render(
      <MyConsultations
        selectedId={OPEN_ITEM.id}
        onSelectionChange={onSelectionChange}
        onSessionLost={vi.fn()}
        onCreate={vi.fn()}
      />,
    );

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Finalize consultation" }),
      ).toBeInTheDocument(),
    );

    await user.click(
      screen.getByRole("button", { name: "Finalize consultation" }),
    );

    const dialog = await screen.findByRole("dialog", {
      name: "Finalize consultation?",
    });
    await user.click(within(dialog).getByRole("checkbox", { name: "Photo 1" }));
    await user.click(
      within(dialog).getByRole("button", { name: "Review finalization" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Finalize consultation" }),
    );

    await waitFor(() =>
      expect(finalizeMock).toHaveBeenCalledWith(
        OPEN_ITEM.id,
        expect.any(String),
        { kind: "selected", option_ids: ["photo-1"] },
      ),
    );

    await waitFor(() =>
      expect(
        screen.getByText("Photos are no longer available."),
      ).toBeInTheDocument(),
    );
    expect(onSelectionChange).not.toHaveBeenCalledWith(null);
  });

  it("shows a retryable error state that is distinct from empty", async () => {
    listMock.mockRejectedValue(new Error("offline"));
    renderList();
    await waitFor(() =>
      expect(
        screen.getByText("Could not load your consultations."),
      ).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(
      screen.queryByText("You have no open consultations."),
    ).not.toBeInTheDocument();
  });

  it("appends the next page on Load more", async () => {
    listMock
      .mockResolvedValueOnce({ items: [OPEN_ITEM], next_cursor: "cursor-1" })
      .mockResolvedValueOnce({ items: [FINALIZED_ITEM], next_cursor: null });
    const user = userEvent.setup();
    renderList();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: "Load more" }));

    await waitFor(() =>
      expect(
        screen.getByText(`Consultation ${FINALIZED_ITEM.id}`),
      ).toBeInTheDocument(),
    );
  });

  it("deduplicates repeated IDs both across pages and inside the next page", async () => {
    const nextItem = {
      ...OPEN_ITEM,
      id: FINALIZED_ITEM.id,
      question: "Another choice?",
    };
    listMock
      .mockResolvedValueOnce({ items: [OPEN_ITEM], next_cursor: "cursor-1" })
      .mockResolvedValueOnce({
        items: [OPEN_ITEM, nextItem, nextItem],
        next_cursor: null,
      });
    renderList();
    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Load more" }));
    await waitFor(() =>
      expect(
        screen.getAllByRole("button", { name: "View consultation" }),
      ).toHaveLength(2),
    );
    expect(screen.getAllByText("Another choice?")).toHaveLength(1);
  });

  it("opens the owner detail when View consultation is selected", async () => {
    listMock.mockResolvedValue({ items: [OPEN_ITEM], next_cursor: null });
    const onSelectionChange = vi.fn();
    const user = userEvent.setup();
    renderList({ onSelectionChange });

    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );
    await user.click(screen.getByRole("button", { name: "View consultation" }));

    expect(onSelectionChange).toHaveBeenCalledWith(OPEN_ITEM.id);
  });

  it("renders the selected returning detail", async () => {
    render(
      <MyConsultations
        selectedId={OPEN_ITEM.id}
        onSelectionChange={vi.fn()}
        onSessionLost={vi.fn()}
        onCreate={vi.fn()}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "Your consultation" }),
      ).toBeInTheDocument(),
    );
    expect(detailMock).toHaveBeenCalledWith(OPEN_ITEM.id);
  });

  it("delegates session loss to the parent", async () => {
    listMock.mockRejectedValue(new ApiError("unauthenticated"));
    const onSessionLost = vi.fn();
    renderList({ onSessionLost });
    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });

  it("does not report session loss from a list request after unmount", async () => {
    let rejectList: (error: unknown) => void = () => undefined;
    listMock.mockReturnValue(
      new Promise((_, reject) => {
        rejectList = reject;
      }),
    );
    const onSessionLost = vi.fn();
    const { unmount } = renderList({ onSessionLost });

    unmount();
    rejectList(new ApiError("unauthenticated"));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(onSessionLost).not.toHaveBeenCalled();
  });

  it("ignores a late list response after switching to detail", async () => {
    let rejectList: (error: unknown) => void = () => undefined;
    listMock.mockReturnValue(
      new Promise((_, reject) => {
        rejectList = reject;
      }),
    );
    const onSessionLost = vi.fn();
    const { rerender } = render(
      <MyConsultations
        selectedId={null}
        onSelectionChange={vi.fn()}
        onSessionLost={onSessionLost}
        onCreate={vi.fn()}
      />,
    );

    rerender(
      <MyConsultations
        selectedId="123e4567-e89b-12d3-a456-426614174000"
        onSelectionChange={vi.fn()}
        onSessionLost={onSessionLost}
        onCreate={vi.fn()}
      />,
    );

    rejectList(new ApiError("unauthenticated"));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(onSessionLost).not.toHaveBeenCalled();
  });

  it("resets pending refresh state when switching tabs during a refresh", async () => {
    const user = userEvent.setup();
    listMock.mockResolvedValue({ items: [], next_cursor: null });
    renderList();
    await waitFor(() =>
      expect(
        screen.getByText("You have no open consultations."),
      ).toBeInTheDocument(),
    );

    let resolveRefresh: (value: unknown) => void = () => undefined;
    listMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveRefresh = resolve;
        }),
    );

    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(
      screen.getByRole("button", { name: "Refreshing…" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Finalized" }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Refresh" })).toBeEnabled(),
    );
    resolveRefresh({ items: [], next_cursor: null });
  });

  it("retries a failed later page and preserves loaded rows", async () => {
    const user = userEvent.setup();
    listMock
      .mockResolvedValueOnce({ items: [OPEN_ITEM], next_cursor: "cursor-1" })
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ items: [FINALIZED_ITEM], next_cursor: null });
    renderList();

    await waitFor(() =>
      expect(screen.getByText("Which one?")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: "Load more" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Try loading more" }),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("Which one?")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Try loading more" }));
    await waitFor(() =>
      expect(
        screen.getByText(`Consultation ${FINALIZED_ITEM.id}`),
      ).toBeInTheDocument(),
    );
  });

  it("shows feedback when refreshing an empty list fails", async () => {
    const user = userEvent.setup();
    listMock.mockResolvedValue({ items: [], next_cursor: null });
    renderList();
    await waitFor(() =>
      expect(
        screen.getByText("You have no open consultations."),
      ).toBeInTheDocument(),
    );

    listMock.mockRejectedValueOnce(new Error("offline"));
    await user.click(screen.getByRole("button", { name: "Refresh" }));

    await waitFor(() =>
      expect(
        screen.getByText("Could not refresh your consultations."),
      ).toBeInTheDocument(),
    );
  });

  it("associates tabs with an accessible tabpanel", async () => {
    renderList();
    const openTab = screen.getByRole("tab", { name: "Open" });
    const panel = screen.getByRole("tabpanel");
    expect(openTab).toHaveAttribute("aria-controls", panel.id);
    expect(panel).toHaveAttribute("aria-labelledby", openTab.id);
    expect(openTab).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Finalized" })).toHaveAttribute(
      "tabindex",
      "-1",
    );
  });

  it("supports arrow-key tab navigation with roving focus", async () => {
    const user = userEvent.setup();
    renderList();
    const openTab = screen.getByRole("tab", { name: "Open" });
    const finalizedTab = screen.getByRole("tab", { name: "Finalized" });

    openTab.focus();
    await user.keyboard("{ArrowRight}");
    expect(finalizedTab).toHaveFocus();
    expect(finalizedTab).toHaveAttribute("aria-selected", "true");
    await waitFor(() =>
      expect(listMock).toHaveBeenLastCalledWith("finalized", 20, null),
    );

    await user.keyboard("{ArrowRight}");
    expect(openTab).toHaveFocus();
    expect(openTab).toHaveAttribute("aria-selected", "true");

    await user.keyboard("{ArrowLeft}");
    expect(finalizedTab).toHaveFocus();

    await user.keyboard("{End}");
    expect(finalizedTab).toHaveFocus();

    await user.keyboard("{Home}");
    expect(openTab).toHaveFocus();
  });

  it("shows the current total vote count on each open row", async () => {
    listMock.mockResolvedValue({
      items: [
        { ...OPEN_ITEM, total_votes: 1 },
        {
          ...OPEN_ITEM,
          id: "123e4567-e89b-12d3-a456-426614174002",
          total_votes: 2,
        },
      ],
      next_cursor: null,
    });
    renderList();
    await waitFor(() => expect(screen.getByText("1 vote")).toBeInTheDocument());
    expect(screen.getByText("2 votes")).toBeInTheDocument();
  });

  it("auto-refreshes the open list every five seconds while visible", async () => {
    vi.useFakeTimers();
    try {
      listMock.mockResolvedValue({ items: [OPEN_ITEM], next_cursor: null });
      renderList();
      await act(async () => {});
      expect(listMock).toHaveBeenCalledTimes(1);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(5000);
      });
      expect(listMock).toHaveBeenCalledTimes(2);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(5000);
      });
      expect(listMock).toHaveBeenCalledTimes(3);
    } finally {
      vi.useRealTimers();
    }
  });

  it("does not auto-refresh the finalized list", async () => {
    vi.useFakeTimers();
    try {
      listMock.mockResolvedValue({ items: [], next_cursor: null });
      renderList();
      await act(async () => {});
      fireEvent.click(screen.getByRole("tab", { name: "Finalized" }));
      await act(async () => {});
      const callsAfterSwitch = listMock.mock.calls.length;

      await act(async () => {
        await vi.advanceTimersByTimeAsync(15000);
      });
      expect(listMock.mock.calls.length).toBe(callsAfterSwitch);
    } finally {
      vi.useRealTimers();
    }
  });
});

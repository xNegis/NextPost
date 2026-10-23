import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  fetchParticipationHistory,
  type ParticipationItem,
} from "./consultationApi";
import { MyParticipation } from "./MyParticipation";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchParticipationHistory: vi.fn(),
  };
});

const fetchMock = vi.mocked(fetchParticipationHistory);

const UUID = "123e4567-e89b-12d3-a456-426614174000";

function item(overrides: Partial<ParticipationItem> = {}): ParticipationItem {
  return {
    consultation_id: UUID,
    status: "open",
    event_kind: "voted",
    event_at: "2026-10-21T12:00:00Z",
    can_view: true,
    ...overrides,
  };
}

function renderList(
  props: Partial<Parameters<typeof MyParticipation>[0]> = {},
) {
  return render(
    <MyParticipation
      onSessionLost={vi.fn()}
      onViewConsultation={vi.fn()}
      onGoHome={vi.fn()}
      {...props}
    />,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  fetchMock.mockResolvedValue({ items: [], next_cursor: null });
});

describe("MyParticipation", () => {
  it("shows a labelled loading state while the first request is pending", async () => {
    fetchMock.mockReturnValueOnce(new Promise(() => {}));
    renderList();

    expect(
      await screen.findByText("Loading your participation…"),
    ).toBeInTheDocument();
  });

  it("renders the empty state with a Home action", async () => {
    const onGoHome = vi.fn();
    renderList({ onGoHome });

    expect(
      await screen.findByText("Consultations you vote in will appear here."),
    ).toBeInTheDocument();
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Go to Home" }));
    expect(onGoHome).toHaveBeenCalledTimes(1);
  });

  it("offers a retry that recovers from an initial failure", async () => {
    fetchMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ items: [], next_cursor: null });

    renderList();

    await userEvent.click(await screen.findByRole("button", { name: "Retry" }));
    await screen.findByText("Consultations you vote in will appear here.");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("shows the neutral explanation copy", async () => {
    fetchMock.mockResolvedValueOnce({ items: [item()], next_cursor: null });
    renderList();

    expect(
      await screen.findByText(/compares your vote with the author/i),
    ).toBeInTheDocument();
  });

  it.each([
    ["open", "Open", "voted"],
    ["matched", "Matched", "finalized"],
    ["not_matched", "Not matched", "finalized"],
    ["no_choice", "No choice", "finalized"],
    ["unavailable", "Unavailable", "voted"],
  ] as const)(
    "renders status %s with the right label and kind",
    async (status, label, kind) => {
      fetchMock.mockResolvedValueOnce({
        items: [item({ status, event_kind: kind, can_view: false })],
        next_cursor: null,
      });
      renderList();

      expect(await screen.findByText(label)).toBeInTheDocument();
      expect(
        screen.getByText(
          new RegExp(`^${kind === "voted" ? "Voted" : "Finalized"}`),
        ),
      ).toBeInTheDocument();
    },
  );

  it("explains No choice as the author declaring none", async () => {
    fetchMock.mockResolvedValueOnce({
      items: [
        item({ status: "no_choice", event_kind: "finalized", can_view: false }),
      ],
      next_cursor: null,
    });
    renderList();

    expect(
      await screen.findByText(/The author declared no selected photo/i),
    ).toBeInTheDocument();
  });

  it("shows a View consultation action only for a server-authorised public open row", async () => {
    const onViewConsultation = vi.fn();
    fetchMock.mockResolvedValueOnce({
      items: [item({ status: "open", can_view: true })],
      next_cursor: null,
    });
    renderList({ onViewConsultation });

    const viewButton = await screen.findByRole("button", {
      name: "View consultation",
    });
    await userEvent.setup().click(viewButton);
    expect(onViewConsultation).toHaveBeenCalledWith(UUID);
  });

  it("offers no View action for a non-public row", async () => {
    fetchMock.mockResolvedValueOnce({
      items: [item({ status: "open", can_view: false })],
      next_cursor: null,
    });
    renderList();

    await screen.findByText("Open");
    expect(
      screen.queryByRole("button", { name: "View consultation" }),
    ).not.toBeInTheDocument();
  });

  it("renders no photo, option or aggregate content", async () => {
    fetchMock.mockResolvedValueOnce({
      items: [
        item({ status: "matched", event_kind: "finalized", can_view: false }),
      ],
      next_cursor: null,
    });
    renderList();

    await screen.findByText("Matched");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByText(/votes/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Which one\?/i)).not.toBeInTheDocument();
  });

  it("loads more pages and deduplicates by consultation id", async () => {
    fetchMock
      .mockResolvedValueOnce({ items: [item()], next_cursor: "cursor-1" })
      .mockResolvedValueOnce({
        items: [
          item({
            consultation_id: "123e4567-e89b-12d3-a456-426614174099",
            status: "matched",
            event_kind: "finalized",
            can_view: false,
          }),
        ],
        next_cursor: null,
      });

    renderList();

    await screen.findByText("Open");
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Load more" }));

    await waitFor(() =>
      expect(screen.getByText("Matched")).toBeInTheDocument(),
    );
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("keeps rows and offers a retry when load-more fails", async () => {
    fetchMock
      .mockResolvedValueOnce({ items: [item()], next_cursor: "cursor-1" })
      .mockRejectedValueOnce(new Error("offline"));

    renderList();

    await screen.findByText("Open");
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Load more" }));

    expect(
      await screen.findByRole("button", { name: "Try loading more" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Open")).toBeInTheDocument();
  });

  it("returns to sign-in when the session is no longer valid", async () => {
    const onSessionLost = vi.fn();
    fetchMock.mockRejectedValueOnce(new ApiError("unauthenticated"));

    renderList({ onSessionLost });

    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });
});

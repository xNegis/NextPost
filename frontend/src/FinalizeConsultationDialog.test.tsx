import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { finalizeConsultation } from "./consultationApi";
import { FinalizeConsultationDialog } from "./FinalizeConsultationDialog";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return { ...actual, finalizeConsultation: vi.fn() };
});

const finalizeConsultationMock = vi.mocked(finalizeConsultation);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";
const PHOTOS = [
  { id: "123e4567-e89b-12d3-a456-426614174002", width: 100, height: 200 },
  { id: "123e4567-e89b-12d3-a456-426614174003", width: 100, height: 200 },
];
const PHOTO_URLS = ["blob:photo-1", "blob:photo-2"];

function renderDialog(
  overrides: Partial<Parameters<typeof FinalizeConsultationDialog>[0]> = {},
) {
  const props = {
    consultationId: CONSULTATION_ID,
    photos: PHOTOS,
    photoUrls: PHOTO_URLS,
    onCancel: vi.fn(),
    onFinalized: vi.fn(),
    onReload: vi.fn(),
    onSessionLost: vi.fn(),
    ...overrides,
  };
  const utils = render(<FinalizeConsultationDialog {...props} />);
  return { props, ...utils };
}

async function advanceToReview(
  user: ReturnType<typeof userEvent.setup>,
  names: string[],
): Promise<void> {
  for (const name of names) {
    await user.click(screen.getByRole("checkbox", { name }));
  }
  await user.click(screen.getByRole("button", { name: "Review finalization" }));
}

beforeEach(() => {
  vi.clearAllMocks();
  finalizeConsultationMock.mockResolvedValue({
    id: CONSULTATION_ID,
    state: "finalized",
    published_at: "2026-09-28T12:00:00Z",
    result: null,
  });
});

describe("FinalizeConsultationDialog", () => {
  it("has an accessible name and description", () => {
    renderDialog();
    const dialog = screen.getByRole("dialog", {
      name: "Finalize consultation?",
    });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(screen.getByText(/Finalizing is permanent/)).toBeInTheDocument();
  });

  it("starts in the selection step and disables Review until a selection is made", () => {
    renderDialog();
    expect(
      screen.getByRole("button", { name: "Review finalization" }),
    ).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: "Finalize consultation" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Consultation photo 1" }),
    ).toHaveAttribute("src", PHOTO_URLS[0]);
    expect(screen.getByText("Photo 1 of 2")).toBeInTheDocument();
  });

  it("moves to a review step that summarizes the choice before finalizing", async () => {
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByRole("checkbox", { name: "Photo 1" }));
    await user.click(
      screen.getByRole("button", { name: "Review finalization" }),
    );

    expect(screen.getByText("Your choice: Photo 1")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Selected consultation photo 1" }),
    ).toHaveAttribute("src", PHOTO_URLS[0]);
    expect(
      screen.getByRole("button", { name: "Finalize consultation" }),
    ).toBeEnabled();
    expect(screen.getByRole("button", { name: "Back" })).toBeInTheDocument();
  });

  it("returns to the selection step from review with Back", async () => {
    const user = userEvent.setup();
    renderDialog();
    await advanceToReview(user, ["Photo 1"]);
    await user.click(screen.getByRole("button", { name: "Back" }));

    expect(screen.getByRole("checkbox", { name: "Photo 1" })).toBeChecked();
    expect(
      screen.getByRole("button", { name: "Review finalization" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Finalize consultation" }),
    ).not.toBeInTheDocument();
  });

  it("sends a selected declaration with the chosen photos", async () => {
    const user = userEvent.setup();
    const { props } = renderDialog();
    await user.click(screen.getByRole("checkbox", { name: "Photo 1" }));
    await user.click(screen.getByRole("checkbox", { name: "Photo 2" }));

    expect(
      screen.getByText("Your choice: Photo 1, Photo 2"),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Review finalization" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Finalize consultation" }),
    );

    await waitFor(() =>
      expect(finalizeConsultationMock).toHaveBeenCalledWith(
        CONSULTATION_ID,
        expect.any(String),
        { kind: "selected", option_ids: [PHOTOS[0].id, PHOTOS[1].id] },
      ),
    );
    expect(props.onFinalized).toHaveBeenCalledTimes(1);
  });

  it("sends a none declaration with no option ids", async () => {
    const user = userEvent.setup();
    const { props } = renderDialog();
    await user.click(screen.getByRole("checkbox", { name: "Choose none" }));

    expect(screen.getByText("Your choice: No choice")).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Review finalization" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Finalize consultation" }),
    );

    await waitFor(() =>
      expect(finalizeConsultationMock).toHaveBeenCalledWith(
        CONSULTATION_ID,
        expect.any(String),
        { kind: "none", option_ids: [] },
      ),
    );
    expect(props.onFinalized).toHaveBeenCalledTimes(1);
  });

  it("clears selected photos when none is chosen and vice versa", async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByRole("checkbox", { name: "Photo 1" }));
    expect(screen.getByRole("checkbox", { name: "Photo 1" })).toBeChecked();

    await user.click(screen.getByRole("checkbox", { name: "Choose none" }));
    expect(screen.getByRole("checkbox", { name: "Photo 1" })).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Choose none" })).toBeChecked();

    await user.click(screen.getByRole("checkbox", { name: "Photo 2" }));
    expect(
      screen.getByRole("checkbox", { name: "Choose none" }),
    ).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Photo 2" })).toBeChecked();
  });

  it("puts initial focus on the safe Cancel action", async () => {
    renderDialog();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus(),
    );
  });

  it("cancels on Escape", async () => {
    const { props } = renderDialog();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus(),
    );
    await userEvent.keyboard("{Escape}");
    expect(props.onCancel).toHaveBeenCalledTimes(1);
  });

  it("cancels via the Cancel button", async () => {
    const user = userEvent.setup();
    const { props } = renderDialog();
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(props.onCancel).toHaveBeenCalledTimes(1);
  });

  it("does not double-submit while pending", async () => {
    const user = userEvent.setup();
    let resolve!: () => void;
    finalizeConsultationMock.mockReturnValue(
      new Promise((resolvePromise) => {
        resolve = resolvePromise;
      }),
    );

    renderDialog();
    await advanceToReview(user, ["Photo 1"]);
    const confirm = screen.getByRole("button", {
      name: "Finalize consultation",
    });
    await user.click(confirm);
    expect(screen.getByRole("button", { name: "Finalizing…" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Finalizing…" }));

    expect(finalizeConsultationMock).toHaveBeenCalledTimes(1);
    resolve();
    await waitFor(() =>
      expect(finalizeConsultationMock).toHaveBeenCalledTimes(1),
    );
  });

  it("preserves the operation id and selection across a retryable failure", async () => {
    const user = userEvent.setup();
    finalizeConsultationMock
      .mockRejectedValueOnce(new ApiError("network"))
      .mockResolvedValueOnce({
        id: CONSULTATION_ID,
        state: "finalized",
        published_at: "2026-09-28T12:00:00Z",
        result: null,
      });

    renderDialog();
    await advanceToReview(user, ["Photo 1"]);

    const confirm = screen.getByRole("button", {
      name: "Finalize consultation",
    });
    await user.click(confirm);
    await waitFor(() =>
      expect(
        screen.getByText("Could not finalize the consultation. Try again."),
      ).toBeInTheDocument(),
    );

    await user.click(
      screen.getByRole("button", { name: "Finalize consultation" }),
    );
    await waitFor(() =>
      expect(finalizeConsultationMock).toHaveBeenCalledTimes(2),
    );

    const firstOperationId = finalizeConsultationMock.mock.calls[0][1];
    const secondOperationId = finalizeConsultationMock.mock.calls[1][1];
    expect(secondOperationId).toBe(firstOperationId);
    expect(finalizeConsultationMock.mock.calls[1][2]).toEqual({
      kind: "selected",
      option_ids: [PHOTOS[0].id],
    });
  });

  it("reloads the detail on a stale-state conflict", async () => {
    const user = userEvent.setup();
    finalizeConsultationMock.mockRejectedValueOnce(
      new ApiError("consultation_conflict"),
    );
    const { props } = renderDialog();

    await advanceToReview(user, ["Photo 1"]);
    await user.click(
      screen.getByRole("button", { name: "Finalize consultation" }),
    );
    await waitFor(() => expect(props.onReload).toHaveBeenCalledTimes(1));
  });

  it("reloads the detail when the target became unavailable", async () => {
    const user = userEvent.setup();
    finalizeConsultationMock.mockRejectedValueOnce(
      new ApiError("consultation_unavailable"),
    );
    const { props } = renderDialog();

    await advanceToReview(user, ["Photo 1"]);
    await user.click(
      screen.getByRole("button", { name: "Finalize consultation" }),
    );
    await waitFor(() => expect(props.onReload).toHaveBeenCalledTimes(1));
  });

  it("delegates session loss", async () => {
    const user = userEvent.setup();
    finalizeConsultationMock.mockRejectedValueOnce(
      new ApiError("unauthenticated"),
    );
    const { props } = renderDialog();

    await advanceToReview(user, ["Photo 1"]);
    await user.click(
      screen.getByRole("button", { name: "Finalize consultation" }),
    );
    await waitFor(() => expect(props.onSessionLost).toHaveBeenCalledTimes(1));
  });

  it("contains Tab focus within the dialog", async () => {
    renderDialog();
    const chooseNone = screen.getByRole("checkbox", { name: "Choose none" });
    chooseNone.focus();
    await waitFor(() => expect(chooseNone).toHaveFocus());

    // Shift+Tab from the first element wraps to the last focusable element.
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();

    // Tab from the last element wraps back to the first.
    fireEvent.keyDown(document, { key: "Tab" });
    expect(chooseNone).toHaveFocus();
  });
});

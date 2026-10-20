import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { deleteConsultation } from "./consultationApi";
import { DeleteConsultationDialog } from "./DeleteConsultationDialog";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return { ...actual, deleteConsultation: vi.fn() };
});

const deleteConsultationMock = vi.mocked(deleteConsultation);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";

function renderDialog(
  state: "open" | "finalized" = "open",
  overrides: Partial<Parameters<typeof DeleteConsultationDialog>[0]> = {},
) {
  const props = {
    consultationId: CONSULTATION_ID,
    state,
    onCancel: vi.fn(),
    onDeleted: vi.fn(),
    onReload: vi.fn(),
    onSessionLost: vi.fn(),
    ...overrides,
  };
  const utils = render(<DeleteConsultationDialog {...props} />);
  return { props, ...utils };
}

beforeEach(() => {
  vi.clearAllMocks();
  deleteConsultationMock.mockResolvedValue(undefined);
});

describe("DeleteConsultationDialog", () => {
  it("has an accessible name and description", () => {
    renderDialog();
    const dialog = screen.getByRole("dialog", { name: "Delete consultation?" });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(
      screen.getByText(
        /Access ends immediately\. Every photograph is permanently scheduled for deletion/,
      ),
    ).toBeInTheDocument();
  });

  it("shows the finalized-specific warning", () => {
    renderDialog("finalized");
    expect(
      screen.getByText(
        /This consultation will disappear from My consultations/,
      ),
    ).toBeInTheDocument();
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

  it("confirms with the exact state and reports success", async () => {
    const user = userEvent.setup();
    const { props } = renderDialog("open");
    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    await waitFor(() =>
      expect(deleteConsultationMock).toHaveBeenCalledWith(
        CONSULTATION_ID,
        "open",
      ),
    );
    expect(props.onDeleted).toHaveBeenCalledTimes(1);
  });

  it("sends the finalized state when withdrawing", async () => {
    const user = userEvent.setup();
    const { props } = renderDialog("finalized");
    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    await waitFor(() =>
      expect(deleteConsultationMock).toHaveBeenCalledWith(
        CONSULTATION_ID,
        "finalized",
      ),
    );
    expect(props.onDeleted).toHaveBeenCalledTimes(1);
  });

  it("locks the pending state and does not double-submit", async () => {
    const user = userEvent.setup();
    let resolve!: () => void;
    deleteConsultationMock.mockReturnValue(
      new Promise((resolvePromise) => {
        resolve = resolvePromise;
      }),
    );

    renderDialog();
    const confirm = screen.getByRole("button", {
      name: "Delete consultation",
    });
    await user.click(confirm);
    expect(screen.getByRole("button", { name: "Deleting…" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Deleting…" }));

    expect(deleteConsultationMock).toHaveBeenCalledTimes(1);
    resolve();
    await waitFor(() =>
      expect(deleteConsultationMock).toHaveBeenCalledTimes(1),
    );
  });

  it("keeps the dialog usable and shows a retry message on pre-commit failure", async () => {
    const user = userEvent.setup();
    deleteConsultationMock.mockRejectedValueOnce(new ApiError("network"));
    const { props } = renderDialog();

    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    await waitFor(() =>
      expect(
        screen.getByText("Could not delete the consultation. Try again."),
      ).toBeInTheDocument(),
    );
    expect(props.onDeleted).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Delete consultation" }),
    ).toBeEnabled();
  });

  it("reloads the detail on a stale-state conflict", async () => {
    const user = userEvent.setup();
    deleteConsultationMock.mockRejectedValueOnce(
      new ApiError("consultation_conflict"),
    );
    const { props } = renderDialog();

    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    await waitFor(() => expect(props.onReload).toHaveBeenCalledTimes(1));
    expect(props.onDeleted).not.toHaveBeenCalled();
  });

  it("reloads the detail when the target became unavailable", async () => {
    const user = userEvent.setup();
    deleteConsultationMock.mockRejectedValueOnce(
      new ApiError("consultation_unavailable"),
    );
    const { props } = renderDialog();

    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    await waitFor(() => expect(props.onReload).toHaveBeenCalledTimes(1));
  });

  it("delegates session loss", async () => {
    const user = userEvent.setup();
    deleteConsultationMock.mockRejectedValueOnce(
      new ApiError("unauthenticated"),
    );
    const { props } = renderDialog();

    await user.click(
      screen.getByRole("button", { name: "Delete consultation" }),
    );
    await waitFor(() => expect(props.onSessionLost).toHaveBeenCalledTimes(1));
  });

  it("contains Tab focus within the dialog", async () => {
    renderDialog();
    const cancel = screen.getByRole("button", { name: "Cancel" });
    const confirm = screen.getByRole("button", {
      name: "Delete consultation",
    });
    await waitFor(() => expect(cancel).toHaveFocus());

    // Shift+Tab from the first element wraps to the last.
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(confirm).toHaveFocus();

    // Tab from the last element wraps back to the first.
    fireEvent.keyDown(document, { key: "Tab" });
    expect(cancel).toHaveFocus();
  });

  it("restores focus to the previously focused element on unmount", async () => {
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.textContent = "trigger";
    document.body.appendChild(trigger);
    trigger.focus();

    const view = renderDialog();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus(),
    );

    view.unmount();

    expect(trigger).toHaveFocus();
    trigger.remove();
  });
});

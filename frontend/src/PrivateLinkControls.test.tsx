import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PrivateLinkControls } from "./PrivateLinkControls";

const LINK =
  "https://app.example/consultations/123e4567-e89b-12d3-a456-426614174000#access=v1.AAA";

function renderControls(
  overrides: Partial<Parameters<typeof PrivateLinkControls>[0]> = {},
) {
  const props = {
    status: "active" as const,
    link: LINK,
    pending: false,
    onCopy: vi.fn(),
    onDisable: vi.fn(),
    onReplace: vi.fn(),
    onCreateNew: vi.fn(),
    ...overrides,
  };
  render(<PrivateLinkControls {...props} />);
  return props;
}

describe("PrivateLinkControls", () => {
  it("shows the current link and copy action when active", () => {
    renderControls();

    expect(screen.getByText("Current link")).toBeInTheDocument();
    expect(screen.getByText(LINK)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy link" })).toBeEnabled();
  });

  it("copies the current link", async () => {
    const user = userEvent.setup();
    const props = renderControls();

    await user.click(screen.getByRole("button", { name: "Copy link" }));

    expect(props.onCopy).toHaveBeenCalledWith(LINK);
  });

  it("requires confirmation before disabling", async () => {
    const user = userEvent.setup();
    const props = renderControls();

    await user.click(screen.getByRole("button", { name: "Disable link" }));

    expect(
      screen.getByRole("heading", { name: "Disable link?" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Disable link" })).toHaveFocus();
    expect(props.onDisable).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Disable link" }));

    expect(props.onDisable).toHaveBeenCalledTimes(1);
  });

  it("cancelling a disable changes nothing", async () => {
    const user = userEvent.setup();
    const props = renderControls();

    await user.click(screen.getByRole("button", { name: "Disable link" }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(props.onDisable).not.toHaveBeenCalled();
    expect(screen.getByText("Current link")).toBeInTheDocument();
  });

  it("requires confirmation before replacing", async () => {
    const user = userEvent.setup();
    const props = renderControls();

    await user.click(screen.getByRole("button", { name: "Replace link" }));

    expect(
      screen.getByRole("heading", { name: "Replace link?" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Replace link" })).toHaveFocus();
    expect(props.onReplace).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Replace link" }));

    expect(props.onReplace).toHaveBeenCalledTimes(1);
  });

  it("shows disabled state and allows creating a new link", async () => {
    const user = userEvent.setup();
    const props = renderControls({ status: "disabled", link: null });

    expect(screen.getByText("Link disabled")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Create new link" }));

    expect(props.onCreateNew).toHaveBeenCalledTimes(1);
  });

  it("prevents duplicate actions while pending", () => {
    renderControls({ pending: true });

    expect(screen.getByRole("button", { name: "Copy link" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Disable link" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Replace link" })).toBeDisabled();
  });

  it("offers reconciliation after a mutation error", async () => {
    const user = userEvent.setup();
    const onRefresh = vi.fn();
    renderControls({
      error: "Could not update the private link.",
      onRefresh,
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Could not update the private link.",
    );
    await user.click(screen.getByRole("button", { name: "Refresh link" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});

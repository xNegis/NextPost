import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PublishSummary } from "./PublishSummary";

function renderSummary(
  overrides: Partial<Parameters<typeof PublishSummary>[0]> = {},
) {
  const props = {
    question: "Which one should I post?",
    context: null,
    audience: "public" as const,
    photoCount: 2,
    pending: false,
    error: null,
    onPublish: vi.fn(),
    onBackToEdit: vi.fn(),
    ...overrides,
  };
  render(<PublishSummary {...props} />);
  return props;
}

describe("PublishSummary", () => {
  it("shows the reviewed text and audience reach", () => {
    renderSummary();

    expect(screen.getByText("Which one should I post?")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Anyone with an account can find and see this consultation.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/2 photos will be published/)).toBeInTheDocument();
  });

  it("shows private reach copy for a private consultation", () => {
    renderSummary({ audience: "private" });

    expect(
      screen.getByText(
        "Only people with the link and an account can see this consultation.",
      ),
    ).toBeInTheDocument();
  });

  it("describes immutability and no expiry", () => {
    renderSummary();

    expect(
      screen.getByText(
        /Published content can't be edited, and this consultation doesn't expire/,
      ),
    ).toBeInTheDocument();
  });

  it("offers one publish action and a return to edit", async () => {
    const user = userEvent.setup();
    const props = renderSummary();

    const publishButton = screen.getByRole("button", {
      name: "Publish consultation",
    });
    await user.click(publishButton);
    expect(props.onPublish).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "Back to edit" }));
    expect(props.onBackToEdit).toHaveBeenCalledTimes(1);
  });

  it("disables both actions while pending", () => {
    renderSummary({ pending: true });

    expect(screen.getByRole("button", { name: "Publishing…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Back to edit" })).toBeDisabled();
  });

  it("shows the error and repurposes the primary action as Try again", () => {
    renderSummary({ error: "Could not publish this consultation." });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Could not publish this consultation.",
    );
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
  });
});

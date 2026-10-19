import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ShareConsultation } from "./ShareConsultation";

const LINK =
  "https://app.example/consultations/123e4567-e89b-12d3-a456-426614174000";

function defineClipboard(writeText: (text: string) => Promise<void>) {
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText },
  });
}

function defineShare(
  share: (data: ShareData) => Promise<void>,
  canShare: (data: ShareData) => boolean = () => true,
) {
  Object.defineProperty(navigator, "share", {
    configurable: true,
    value: share,
  });
  Object.defineProperty(navigator, "canShare", {
    configurable: true,
    value: canShare,
  });
}

afterEach(() => {
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: undefined,
  });
  Object.defineProperty(navigator, "share", {
    configurable: true,
    value: undefined,
  });
  Object.defineProperty(navigator, "canShare", {
    configurable: true,
    value: undefined,
  });
});

describe("ShareConsultation", () => {
  it("renders the full URL, a Copy action and no device Share when unsupported", () => {
    render(<ShareConsultation link={LINK} />);

    expect(screen.getByLabelText("Consultation link")).toHaveValue(LINK);
    expect(screen.getByRole("button", { name: "Copy link" })).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: "Share" }),
    ).not.toBeInTheDocument();
  });

  it("copies the link and announces success", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    defineClipboard(writeText);

    render(<ShareConsultation link={LINK} />);
    await user.click(screen.getByRole("button", { name: "Copy link" }));

    expect(writeText).toHaveBeenCalledWith(LINK);
    expect(await screen.findByText("Link copied.")).toBeInTheDocument();
  });

  it("preserves the selectable URL and explains manual copy on failure", async () => {
    const user = userEvent.setup();
    defineClipboard(vi.fn().mockRejectedValue(new Error("denied")));

    render(<ShareConsultation link={LINK} />);
    await user.click(screen.getByRole("button", { name: "Copy link" }));

    expect(
      await screen.findByText(
        "Could not copy the link. Select and copy it manually.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Consultation link")).toHaveValue(LINK);
  });

  it("shows a share-unavailable message when no link is available", () => {
    render(<ShareConsultation link={null} />);

    expect(
      screen.getByText("Share is unavailable right now."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Copy link" }),
    ).not.toBeInTheDocument();
  });

  it("shows device Share only when canShare accepts the exact payload", () => {
    const reject = (): boolean => false;
    defineShare(vi.fn().mockResolvedValue(undefined), reject);

    render(<ShareConsultation link={LINK} />);
    expect(
      screen.queryByRole("button", { name: "Share" }),
    ).not.toBeInTheDocument();
  });

  it("sends the generic payload and announces only completion", async () => {
    const user = userEvent.setup();
    const share = vi.fn().mockResolvedValue(undefined);
    defineShare(share);

    render(<ShareConsultation link={LINK} />);
    await user.click(screen.getByRole("button", { name: "Share" }));

    expect(share).toHaveBeenCalledWith({
      title: "NextPost",
      text: "Vote on a photo consultation in NextPost",
      url: LINK,
    });
    expect(await screen.findByText("Share completed.")).toBeInTheDocument();
  });

  it("treats user cancellation of the share sheet neutrally", async () => {
    const user = userEvent.setup();
    const abort = new DOMException("cancelled", "AbortError");
    defineShare(vi.fn().mockRejectedValue(abort));

    render(<ShareConsultation link={LINK} />);
    await user.click(screen.getByRole("button", { name: "Share" }));

    expect(screen.queryByText("Share completed.")).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("reports a share failure while Copy remains usable", async () => {
    const user = userEvent.setup();
    defineShare(vi.fn().mockRejectedValue(new Error("no targets")));

    render(<ShareConsultation link={LINK} />);
    await user.click(screen.getByRole("button", { name: "Share" }));

    expect(
      await screen.findByText("Could not share. Try copying the link instead."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy link" })).toBeEnabled();
  });

  it("recovers when the device Share API throws synchronously", async () => {
    const user = userEvent.setup();
    defineShare(
      vi.fn(() => {
        throw new TypeError("invalid share payload");
      }),
    );

    render(<ShareConsultation link={LINK} />);
    await user.click(screen.getByRole("button", { name: "Share" }));

    expect(
      await screen.findByText("Could not share. Try copying the link instead."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Share" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Copy link" })).toBeEnabled();
  });

  it("prevents duplicate Share activation while the share sheet is pending", async () => {
    const user = userEvent.setup();
    let completeShare: (() => void) | undefined;
    defineShare(
      vi.fn(
        () =>
          new Promise<void>((resolve) => {
            completeShare = resolve;
          }),
      ),
    );

    render(<ShareConsultation link={LINK} />);
    const shareButton = screen.getByRole("button", { name: "Share" });
    await user.click(shareButton);

    expect(screen.getByRole("button", { name: "Sharing…" })).toBeDisabled();
    completeShare?.();
    expect(await screen.findByText("Share completed.")).toBeInTheDocument();
  });
});

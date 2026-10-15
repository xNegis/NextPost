import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConsultationUnavailable } from "./ConsultationUnavailable";

describe("ConsultationUnavailable", () => {
  it("shows the generic unavailable message without a reason", () => {
    render(<ConsultationUnavailable kind="unavailable" onBack={vi.fn()} />);

    expect(
      screen.getByRole("heading", {
        name: "This consultation is unavailable.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/revoked|finalized|deleted|replaced/i),
    ).not.toBeInTheDocument();
  });

  it("offers a way back from the unavailable state", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<ConsultationUnavailable kind="unavailable" onBack={onBack} />);

    await user.click(screen.getByRole("button", { name: "Back to Home" }));

    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("describes a network failure as retryable, not a revocation", () => {
    render(
      <ConsultationUnavailable
        kind="error"
        onBack={vi.fn()}
        onRetry={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Something went wrong." }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/unavailable/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("triggers retry for a retryable failure", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(
      <ConsultationUnavailable
        kind="error"
        onBack={vi.fn()}
        onRetry={onRetry}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});

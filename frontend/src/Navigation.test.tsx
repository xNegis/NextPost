import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Navigation } from "./Navigation";

describe("Navigation", () => {
  it("renders Home and Profile destinations with visible labels", () => {
    render(<Navigation active="home" onSelect={() => {}} />);

    expect(
      screen.getByRole("navigation", { name: "Primary" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Profile" })).toBeInTheDocument();
  });

  it("marks only the active destination with aria-current", () => {
    render(<Navigation active="profile" onSelect={() => {}} />);

    expect(screen.getByRole("button", { name: "Home" })).not.toHaveAttribute(
      "aria-current",
    );
    expect(screen.getByRole("button", { name: "Profile" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("reports the selected destination", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<Navigation active="home" onSelect={onSelect} />);

    await user.click(screen.getByRole("button", { name: "Profile" }));

    expect(onSelect).toHaveBeenCalledWith("profile");
  });
});

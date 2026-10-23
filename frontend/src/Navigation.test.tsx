import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Navigation } from "./Navigation";

describe("Navigation", () => {
  it("renders Home, Create, My consultations, History and Profile with visible labels", () => {
    render(<Navigation active="home" onSelect={() => {}} />);

    expect(
      screen.getByRole("navigation", { name: "Primary" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "My consultations" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "History" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Profile" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(5);
  });

  it("marks the My consultations destination when active", () => {
    render(<Navigation active="my" onSelect={() => {}} />);

    expect(
      screen.getByRole("button", { name: "My consultations" }),
    ).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: "Home" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("marks only the active destination with aria-current", () => {
    render(<Navigation active="create" onSelect={() => {}} />);

    expect(screen.getByRole("button", { name: "Home" })).not.toHaveAttribute(
      "aria-current",
    );
    expect(screen.getByRole("button", { name: "Create" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("button", { name: "Profile" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("reports the selected destination", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<Navigation active="home" onSelect={onSelect} />);

    await user.click(screen.getByRole("button", { name: "Create" }));

    expect(onSelect).toHaveBeenCalledWith("create");
  });

  it("keeps every destination keyboard reachable in display order", async () => {
    const user = userEvent.setup();
    render(<Navigation active="home" onSelect={() => {}} />);

    for (const label of [
      "Home",
      "Create",
      "My consultations",
      "History",
      "Profile",
    ]) {
      await user.tab();
      expect(screen.getByRole("button", { name: label })).toHaveFocus();
    }
  });
});

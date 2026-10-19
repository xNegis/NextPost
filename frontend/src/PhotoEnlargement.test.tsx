import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PhotoEnlargement } from "./PhotoEnlargement";

describe("PhotoEnlargement", () => {
  it("contains keyboard focus inside the dialog", async () => {
    const user = userEvent.setup();
    render(
      <>
        <button>Background action</button>
        <PhotoEnlargement
          src="blob:review"
          alt="Review photo"
          onClose={vi.fn()}
        />
      </>,
    );

    const close = screen.getByRole("button", { name: "Close" });
    expect(close).toHaveFocus();

    await user.tab();
    expect(close).toHaveFocus();

    await user.tab({ shift: true });
    expect(close).toHaveFocus();
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <PhotoEnlargement
        src="blob:review"
        alt="Review photo"
        onClose={onClose}
      />,
    );

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on the Close button", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <PhotoEnlargement
        src="blob:review"
        alt="Review photo"
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

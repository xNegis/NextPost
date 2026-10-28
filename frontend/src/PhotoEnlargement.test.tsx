import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PhotoEnlargement } from "./PhotoEnlargement";

const ITEMS = [
  { id: "one", src: "blob:one", alt: "Review photo 1" },
  { id: "two", src: "blob:two", alt: "Review photo 2" },
];

describe("PhotoEnlargement", () => {
  it("contains keyboard focus inside the dialog", async () => {
    const user = userEvent.setup();
    render(
      <>
        <button>Background action</button>
        <PhotoEnlargement items={ITEMS} initialIndex={0} onClose={vi.fn()} />
      </>,
    );

    const close = screen.getByRole("button", { name: "Close" });
    expect(close).toHaveFocus();

    await user.tab();
    expect(
      screen.getByRole("list", {
        name: "Full-screen consultation photos. Swipe horizontally to browse.",
      }),
    ).toHaveFocus();

    await user.tab({ shift: true });
    expect(close).toHaveFocus();
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <PhotoEnlargement items={ITEMS} initialIndex={0} onClose={onClose} />,
    );

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on the Close button", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <PhotoEnlargement items={ITEMS} initialIndex={0} onClose={onClose} />,
    );

    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("opens at the requested photo and swipes inside full screen", () => {
    render(
      <PhotoEnlargement items={ITEMS} initialIndex={1} onClose={vi.fn()} />,
    );

    expect(screen.getByText("Photo 2 of 2")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Review photo 2" }),
    ).toBeInTheDocument();
    expect(
      screen
        .getByRole("dialog", { name: "Full-screen photo gallery" })
        .querySelectorAll(".photo-carousel__backdrop-image"),
    ).toHaveLength(1);

    const track = screen.getByRole("list", {
      name: "Full-screen consultation photos. Swipe horizontally to browse.",
    });
    Object.defineProperty(track, "clientWidth", { value: 100 });
    Object.defineProperty(track, "scrollLeft", { value: 0 });
    fireEvent.scroll(track);

    expect(screen.getByText("Photo 1 of 2")).toBeInTheDocument();
  });
});

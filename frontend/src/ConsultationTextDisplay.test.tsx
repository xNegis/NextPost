import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConsultationTextDisplay } from "./ConsultationTextDisplay";

describe("ConsultationTextDisplay", () => {
  it("shows the complete question and context in order", () => {
    render(
      <ConsultationTextDisplay question="Which one?" context="Here is why." />,
    );

    const heading = screen.getByRole("heading", { name: "Which one?" });
    const context = screen.getByText("Here is why.");
    expect(heading).toBeInTheDocument();
    expect(context).toBeInTheDocument();
    expect(heading.compareDocumentPosition(context)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });

  it("omits an empty or absent context block", () => {
    const { container, rerender } = render(
      <ConsultationTextDisplay question="Which one?" context={null} />,
    );

    expect(
      container.querySelector(".consultation-text-display__context"),
    ).toBeNull();

    rerender(<ConsultationTextDisplay question="Which one?" context="" />);
    expect(
      container.querySelector(".consultation-text-display__context"),
    ).toBeNull();
  });

  it("preserves paragraph breaks in context", () => {
    const { container } = render(
      <ConsultationTextDisplay
        question="Which one?"
        context={"first\n\nsecond"}
      />,
    );

    const context = container.querySelector(
      ".consultation-text-display__context",
    );
    expect(context).not.toBeNull();
    expect(context?.textContent).toBe("first\n\nsecond");
  });

  it("renders markup and URLs literally without anchors or scripts", () => {
    const markup =
      '<a href="https://example.com">link</a> [md](https://x.example) https://plain.example';
    const { container } = render(
      <ConsultationTextDisplay question={markup} context={markup} />,
    );

    expect(container.querySelector("a")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByRole("heading").textContent).toBe(markup);
    expect(screen.getAllByText(markup)).toHaveLength(2);
  });

  it("accepts a caller-supplied heading level", () => {
    render(
      <ConsultationTextDisplay
        question="Which one?"
        context={null}
        headingLevel={3}
      />,
    );

    expect(
      screen.getByRole("heading", { level: 3, name: "Which one?" }),
    ).toBeInTheDocument();
  });

  it("applies auto direction for RTL text", () => {
    const { container } = render(
      <ConsultationTextDisplay
        question={"\u0645\u0631\u062d\u0628\u0627"}
        context={null}
      />,
    );

    expect(
      container.querySelector(".consultation-text-display__question"),
    ).toHaveAttribute("dir", "auto");
  });
});

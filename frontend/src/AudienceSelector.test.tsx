import { useRef, useState } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  AudienceSelector,
  type AudienceSelectorHandle,
} from "./AudienceSelector";
import type { Audience } from "./audience";

interface HarnessProps {
  initialValue?: Audience | null;
  serverError?: string;
}

function Harness({ initialValue = null, serverError }: HarnessProps) {
  const [value, setValue] = useState<Audience | null>(initialValue);
  const [fieldError, setFieldError] = useState<string | undefined>(serverError);
  const ref = useRef<AudienceSelectorHandle>(null);
  return (
    <div>
      <AudienceSelector
        ref={ref}
        value={value}
        onChange={setValue}
        serverError={fieldError}
        onServerErrorClear={() => setFieldError(undefined)}
      />
      <button type="button" onClick={() => ref.current?.validateAndFocus()}>
        validate
      </button>
    </div>
  );
}

describe("AudienceSelector", () => {
  it("starts with neither option selected", () => {
    render(<Harness />);

    expect(screen.getByLabelText("Public")).not.toBeChecked();
    expect(screen.getByLabelText("Private")).not.toBeChecked();
  });

  it("explains public and private reach", () => {
    render(<Harness />);

    expect(
      screen.getByText(
        "Anyone with an account can find and see it in the feed.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Unlisted. Only people with the link and an account can see it.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Only people who are signed in can see your photos."),
    ).toBeInTheDocument();
  });

  it("reports an error and focuses the first option when empty on validation", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("button", { name: "validate" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Choose an audience.");
    expect(screen.getByLabelText("Public")).toHaveFocus();
  });

  it("selects public and clears the error on correction", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("button", { name: "validate" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Choose an audience.");

    await user.click(screen.getByLabelText("Public"));

    expect(screen.getByLabelText("Public")).toBeChecked();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("keeps the selection across revalidation", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByLabelText("Private"));
    await user.click(screen.getByRole("button", { name: "validate" }));

    expect(screen.getByLabelText("Private")).toBeChecked();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows a server error without changing the selection", () => {
    render(
      <Harness initialValue="public" serverError="Choose Public or Private." />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Choose Public or Private.",
    );
    expect(screen.getByLabelText("Public")).toBeChecked();
  });

  it("clears the server error when the selection changes", async () => {
    const user = userEvent.setup();
    render(<Harness serverError="Choose Public or Private." />);

    await user.click(screen.getByLabelText("Private"));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Private")).toBeChecked();
  });

  it("keeps separate selector instances in independent radio groups", async () => {
    const user = userEvent.setup();
    render(
      <div>
        <Harness />
        <Harness />
      </div>,
    );
    const publicOptions = screen.getAllByLabelText("Public");
    const privateOptions = screen.getAllByLabelText("Private");

    await user.click(publicOptions[0]);
    await user.click(privateOptions[1]);

    expect(publicOptions[0]).toBeChecked();
    expect(privateOptions[1]).toBeChecked();
  });
});

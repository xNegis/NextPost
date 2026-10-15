import { useRef, useState } from "react";

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  ConsultationTextFields,
  type ConsultationTextFieldsHandle,
} from "./ConsultationTextFields";
import { DEFAULT_QUESTION } from "./consultationText";
import type {
  ConsultationTextErrors,
  ConsultationTextLimits,
} from "./consultationText";

const LIMITS: ConsultationTextLimits = { questionMax: 120, contextMax: 500 };

interface HarnessProps {
  initialQuestion?: string;
  initialContext?: string;
  serverErrors?: ConsultationTextErrors;
}

function Harness({
  initialQuestion = DEFAULT_QUESTION,
  initialContext = "",
  serverErrors,
}: HarnessProps) {
  const [question, setQuestion] = useState(initialQuestion);
  const [context, setContext] = useState(initialContext);
  const [fieldErrors, setFieldErrors] = useState(serverErrors);
  const ref = useRef<ConsultationTextFieldsHandle>(null);
  return (
    <div>
      <ConsultationTextFields
        ref={ref}
        question={question}
        context={context}
        limits={LIMITS}
        onQuestionChange={setQuestion}
        onContextChange={setContext}
        serverErrors={fieldErrors}
        onServerErrorClear={(field) =>
          setFieldErrors((previous) => {
            const next = { ...previous };
            delete next[field];
            return next;
          })
        }
      />
      <button type="button" onClick={() => ref.current?.validateAndFocus()}>
        validate
      </button>
    </div>
  );
}

describe("ConsultationTextFields", () => {
  it("renders the question with a normalized counter", () => {
    render(<Harness />);

    const question = screen.getByLabelText("Question");
    expect(question).toHaveValue(DEFAULT_QUESTION);
    expect(screen.getByText("27 / 120")).toBeInTheDocument();
  });

  it("starts context empty with a zero counter and guidance", () => {
    render(<Harness />);

    expect(screen.getByLabelText("Context (optional)")).toHaveValue("");
    expect(screen.getByText("0 / 500")).toBeInTheDocument();
  });

  it("keeps a cleared question empty and requires correction on blur", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const question = screen.getByLabelText("Question");
    await user.clear(question);

    expect(question).toHaveValue("");
    await user.tab();

    expect(screen.getByRole("alert")).toHaveTextContent("Enter a question.");
    expect(question).toHaveValue("");
  });

  it("does not restore the default question", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const question = screen.getByLabelText("Question");
    await user.clear(question);
    await user.click(screen.getByRole("button", { name: "validate" }));

    expect(question).toHaveValue("");
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a question.");
  });

  it("focuses the first invalid field on validation", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.clear(screen.getByLabelText("Question"));
    await user.click(screen.getByRole("button", { name: "validate" }));

    expect(screen.getByLabelText("Question")).toHaveFocus();
  });

  it("focuses the context when only it is invalid", async () => {
    const user = userEvent.setup();
    render(<Harness initialContext={"a".repeat(501)} />);

    await user.click(screen.getByRole("button", { name: "validate" }));

    expect(screen.getByLabelText("Context (optional)")).toHaveFocus();
  });

  it("allows overflow without silent truncation and reports the limit", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const question = screen.getByLabelText("Question");
    const overflow = "a".repeat(121);
    await user.clear(question);
    await user.type(question, overflow);
    await user.tab();

    expect(question).toHaveValue(overflow);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Use 120 characters or fewer for the question.",
    );
  });

  it("clears a field error during correction", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const question = screen.getByLabelText("Question");
    await user.clear(question);
    await user.tab();
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a question.");

    await user.type(question, "Fixed");
    await waitFor(() =>
      expect(screen.queryByRole("alert")).not.toBeInTheDocument(),
    );
  });

  it("counts normalized code points, not surrounding whitespace", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const question = screen.getByLabelText("Question");
    await user.clear(question);
    await user.type(question, "  hi  ");

    expect(question).toHaveValue("  hi  ");
    expect(screen.getByText("2 / 120")).toBeInTheDocument();
  });

  it("preserves raw input while deriving the counter", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const context = screen.getByLabelText("Context (optional)");
    await user.type(context, "line1{enter}{enter}line2");

    expect(context).toHaveValue("line1\n\nline2");
    expect(screen.getByText("12 / 500")).toBeInTheDocument();
  });

  it("shows server errors without wiping input", () => {
    render(<Harness serverErrors={{ question: "Enter a question." }} />);

    expect(screen.getByRole("alert")).toHaveTextContent("Enter a question.");
    expect(screen.getByLabelText("Question")).toHaveValue(DEFAULT_QUESTION);
  });

  it("clears a server field error when that field changes", async () => {
    const user = userEvent.setup();
    render(<Harness serverErrors={{ question: "Enter a question." }} />);

    await user.type(screen.getByLabelText("Question"), " more");

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Question")).toHaveValue(
      `${DEFAULT_QUESTION} more`,
    );
  });

  it("reports valid progression without errors", async () => {
    const user = userEvent.setup();
    render(<Harness initialQuestion="  Which one?  " initialContext="  " />);

    await user.click(screen.getByRole("button", { name: "validate" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Question")).toHaveValue("  Which one?  ");
  });
});

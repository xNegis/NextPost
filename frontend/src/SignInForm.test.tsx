import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, signIn } from "./api";
import { SignInForm } from "./SignInForm";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return {
    ...actual,
    signIn: vi.fn(),
  };
});

const signInMock = vi.mocked(signIn);

const VALID_PASSWORD = "correct-horse-battery-staple";

function renderForm() {
  const onSignedIn = vi.fn();
  const onCreateAccount = vi.fn();
  render(
    <SignInForm onSignedIn={onSignedIn} onCreateAccount={onCreateAccount} />,
  );
  return { onSignedIn, onCreateAccount };
}

beforeEach(() => {
  signInMock.mockReset();
});

describe("SignInForm", () => {
  it("shows client validation errors without submitting", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(
      await screen.findByText("Enter an email address."),
    ).toBeInTheDocument();
    expect(screen.getByText("Enter your password.")).toBeInTheDocument();
    expect(signInMock).not.toHaveBeenCalled();
  });

  it("signs in with valid credentials and clears the password", async () => {
    const user = userEvent.setup();
    const { onSignedIn } = renderForm();
    signInMock.mockResolvedValue({ id: "1", alias: "Ana" });

    await user.type(screen.getByLabelText("Email"), "ana@example.com");
    await user.type(screen.getByLabelText("Password"), VALID_PASSWORD);
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() =>
      expect(onSignedIn).toHaveBeenCalledWith({ id: "1", alias: "Ana" }),
    );
    expect(signInMock).toHaveBeenCalledWith({
      email: "ana@example.com",
      password: VALID_PASSWORD,
    });
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });

  it("disables submission while the request is pending", async () => {
    const user = userEvent.setup();
    signInMock.mockReturnValue(new Promise(() => {}));
    renderForm();

    await user.type(screen.getByLabelText("Email"), "ana@example.com");
    await user.type(screen.getByLabelText("Password"), VALID_PASSWORD);
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByRole("button", { name: "Signing in…" })).toBeDisabled();
  });

  it("shows the generic non-enumerating message for invalid credentials", async () => {
    const user = userEvent.setup();
    signInMock.mockRejectedValue(new ApiError("invalid_credentials"));
    renderForm();

    await user.type(screen.getByLabelText("Email"), "ana@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(
      await screen.findByText("Email or password is incorrect."),
    ).toBeInTheDocument();
  });

  it("shows a retryable message and retains the email on a network failure", async () => {
    const user = userEvent.setup();
    signInMock.mockRejectedValue(new ApiError("network"));
    renderForm();

    await user.type(screen.getByLabelText("Email"), "ana@example.com");
    await user.type(screen.getByLabelText("Password"), VALID_PASSWORD);
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(
      await screen.findByText("Could not sign in. Please try again."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveValue("ana@example.com");
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    renderForm();

    const passwordInput = screen.getByLabelText("Password");
    expect(passwordInput).toHaveAttribute("type", "password");

    await user.click(screen.getByRole("button", { name: "Show password" }));

    expect(passwordInput).toHaveAttribute("type", "text");
  });

  it("offers account creation through the secondary action", async () => {
    const user = userEvent.setup();
    const { onCreateAccount } = renderForm();

    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(onCreateAccount).toHaveBeenCalled();
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, createAccount } from "./api";
import { RegistrationForm } from "./RegistrationForm";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return {
    ...actual,
    createAccount: vi.fn(),
  };
});

const createAccountMock = vi.mocked(createAccount);

const VALID_PASSWORD = "correct-horse-battery-staple";

function renderForm() {
  const onRegistered = vi.fn();
  const onBackToSignIn = vi.fn();
  render(
    <RegistrationForm
      onRegistered={onRegistered}
      onBackToSignIn={onBackToSignIn}
    />,
  );
  return { onRegistered, onBackToSignIn };
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Email"), "ana@example.com");
  await user.type(screen.getByLabelText("Alias"), "Ana");
  await user.type(screen.getByLabelText("Password"), VALID_PASSWORD);
  await user.type(screen.getByLabelText("Confirm password"), VALID_PASSWORD);
}

beforeEach(() => {
  createAccountMock.mockReset();
});

describe("RegistrationForm", () => {
  it("shows client validation errors without submitting", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText("Enter an email address."),
    ).toBeInTheDocument();
    expect(createAccountMock).not.toHaveBeenCalled();
  });

  it("reports a password mismatch without submitting", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByLabelText("Email"), "ana@example.com");
    await user.type(screen.getByLabelText("Alias"), "Ana");
    await user.type(screen.getByLabelText("Password"), VALID_PASSWORD);
    await user.type(
      screen.getByLabelText("Confirm password"),
      "different-password",
    );

    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText("The passwords do not match."),
    ).toBeInTheDocument();
    expect(createAccountMock).not.toHaveBeenCalled();
  });

  it("registers a valid account and reports success", async () => {
    const user = userEvent.setup();
    const { onRegistered } = renderForm();
    createAccountMock.mockResolvedValue({ id: "1", alias: "Ana" });

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() =>
      expect(onRegistered).toHaveBeenCalledWith({ id: "1", alias: "Ana" }),
    );
    expect(createAccountMock).toHaveBeenCalledWith({
      email: "ana@example.com",
      alias: "Ana",
      password: VALID_PASSWORD,
    });
  });

  it("disables submission while the request is pending", async () => {
    const user = userEvent.setup();
    createAccountMock.mockReturnValue(new Promise(() => {}));
    renderForm();

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      screen.getByRole("button", { name: "Creating account…" }),
    ).toBeDisabled();
  });

  it("shows the generic non-enumerating message for a duplicate email", async () => {
    const user = userEvent.setup();
    createAccountMock.mockRejectedValue(
      new ApiError("registration_unavailable"),
    );
    renderForm();

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText(
        "Could not create an account with those details. Check them or sign in if you already have an account.",
      ),
    ).toBeInTheDocument();
  });

  it("shows a field error for an unavailable alias", async () => {
    const user = userEvent.setup();
    createAccountMock.mockRejectedValue(new ApiError("alias_unavailable"));
    renderForm();

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText("That alias is not available."),
    ).toBeInTheDocument();
  });

  it("shows a retryable message and retains safe values on a network failure", async () => {
    const user = userEvent.setup();
    createAccountMock.mockRejectedValue(new ApiError("network"));
    renderForm();

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText(
        "Could not complete registration. Please try again.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveValue("ana@example.com");
    expect(screen.getByLabelText("Alias")).toHaveValue("Ana");
  });

  it("toggles password visibility for both password fields", async () => {
    const user = userEvent.setup();
    renderForm();

    const passwordInput = screen.getByLabelText("Password");
    const confirmInput = screen.getByLabelText("Confirm password");
    expect(passwordInput).toHaveAttribute("type", "password");
    expect(confirmInput).toHaveAttribute("type", "password");

    await user.click(
      screen.getAllByRole("button", { name: "Show password" })[0],
    );

    expect(passwordInput).toHaveAttribute("type", "text");
    expect(confirmInput).toHaveAttribute("type", "password");
  });

  it("associates labels with their controls", () => {
    renderForm();

    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Alias")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm password")).toBeInTheDocument();
  });

  it("returns to sign in through the secondary action", async () => {
    const user = userEvent.setup();
    const { onBackToSignIn } = renderForm();

    await user.click(screen.getByRole("button", { name: "Back to sign in" }));

    expect(onBackToSignIn).toHaveBeenCalled();
  });
});

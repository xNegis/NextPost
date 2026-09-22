import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { ApiError, fetchProfile, fetchSession, signOut } from "./api";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return {
    ...actual,
    fetchSession: vi.fn(),
    fetchProfile: vi.fn(),
    signOut: vi.fn(),
  };
});

const fetchSessionMock = vi.mocked(fetchSession);
const fetchProfileMock = vi.mocked(fetchProfile);
const signOutMock = vi.mocked(signOut);

const AUTHENTICATED_SESSION = {
  authenticated: true,
  account: { id: "account-1", alias: "Ana" },
} as const;

beforeEach(() => {
  fetchSessionMock.mockReset();
  fetchProfileMock.mockReset();
  signOutMock.mockReset();
});

describe("App", () => {
  it("shows sign-in as the default view after an unauthenticated session check", async () => {
    fetchSessionMock.mockResolvedValue({ authenticated: false });

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Create your account" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("restores Home for an authenticated session without a sign-out action", async () => {
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Hi, Ana" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Primary" }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Sign out" }),
    ).not.toBeInTheDocument();
  });

  it("shows a retryable unavailable state and retries the session check", async () => {
    const user = userEvent.setup();
    fetchSessionMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ authenticated: false });

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Retry" }));

    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
    expect(fetchSessionMock).toHaveBeenCalledTimes(2);
  });

  it("navigates from sign-in to registration and back", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue({ authenticated: false });

    render(<App />);

    await user.click(
      await screen.findByRole("button", { name: "Create account" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Create your account" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Back to sign in" }));

    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
  });

  it("opens My profile and shows the owner's email and nickname", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Profile" }));

    expect(
      await screen.findByRole("heading", { name: "My profile" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("ana@example.com")).toBeInTheDocument();
    expect(screen.getByText("Ana")).toBeInTheDocument();
    expect(
      screen.getByText("Only you can see this email."),
    ).toBeInTheDocument();
    expect(fetchProfileMock).toHaveBeenCalledTimes(1);
  });

  it("communicates profile loading while the request is pending", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);
    fetchProfileMock.mockReturnValue(new Promise(() => {}));

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Profile" }));

    expect(
      await screen.findByText("Loading your profile…"),
    ).toBeInTheDocument();
  });

  it("offers a retry that recovers from a profile failure", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);
    fetchProfileMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ email: "ana@example.com", nickname: "Ana" });

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Profile" }));
    await user.click(await screen.findByRole("button", { name: "Retry" }));

    expect(await screen.findByText("ana@example.com")).toBeInTheDocument();
    expect(fetchProfileMock).toHaveBeenCalledTimes(2);
  });

  it("returns to sign-in when the profile session is no longer valid", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);
    fetchProfileMock.mockRejectedValue(new ApiError("unauthenticated"));

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Profile" }));

    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("switches from Profile back to Home and retains the welcome content", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Profile" }));
    await screen.findByRole("heading", { name: "My profile" });

    await user.click(screen.getByRole("button", { name: "Home" }));

    expect(
      await screen.findByRole("heading", { name: "Hi, Ana" }),
    ).toBeInTheDocument();
  });

  it("signs out from My profile and returns to sign-in on success", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });
    signOutMock.mockResolvedValue(undefined);

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Profile" }));
    await user.click(await screen.findByRole("button", { name: "Sign out" }));

    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
    expect(signOutMock).toHaveBeenCalledTimes(1);
  });

  it("stays in My profile with feedback when sign-out fails", async () => {
    const user = userEvent.setup();
    fetchSessionMock.mockResolvedValue(AUTHENTICATED_SESSION);
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });
    signOutMock.mockRejectedValue(new Error("offline"));

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Profile" }));
    await user.click(await screen.findByRole("button", { name: "Sign out" }));

    expect(
      await screen.findByText("Could not sign out. Please try again."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "My profile" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeEnabled();
  });
});

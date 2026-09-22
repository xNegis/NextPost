import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, fetchProfile } from "./api";
import { ProfileView } from "./ProfileView";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return {
    ...actual,
    fetchProfile: vi.fn(),
  };
});

const fetchProfileMock = vi.mocked(fetchProfile);

interface RenderProps {
  onSessionLost?: () => void;
  onSignOut?: () => void;
  signingOut?: boolean;
  signOutFailed?: boolean;
}

function renderView(overrides: RenderProps = {}) {
  const onSessionLost = overrides.onSessionLost ?? vi.fn();
  const onSignOut = overrides.onSignOut ?? vi.fn();
  render(
    <ProfileView
      onSessionLost={onSessionLost}
      onSignOut={onSignOut}
      signingOut={overrides.signingOut ?? false}
      signOutFailed={overrides.signOutFailed ?? false}
    />,
  );
  return { onSessionLost, onSignOut };
}

beforeEach(() => {
  fetchProfileMock.mockReset();
});

describe("ProfileView", () => {
  it("shows a loading status while fetching", () => {
    fetchProfileMock.mockReturnValue(new Promise(() => {}));

    renderView();

    expect(screen.getByText("Loading your profile…")).toBeInTheDocument();
  });

  it("shows email, nickname, and the privacy note on success", async () => {
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });

    renderView();

    expect(await screen.findByText("ana@example.com")).toBeInTheDocument();
    expect(screen.getByText("Ana")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Nickname")).toBeInTheDocument();
    expect(
      screen.getByText("Only you can see this email."),
    ).toBeInTheDocument();
  });

  it("shows a retryable error and reloads on retry", async () => {
    const user = userEvent.setup();
    fetchProfileMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ email: "ana@example.com", nickname: "Ana" });

    renderView();

    expect(
      await screen.findByText("Could not load your profile."),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("ana@example.com")).toBeInTheDocument();
    expect(fetchProfileMock).toHaveBeenCalledTimes(2);
  });

  it("reports a lost session on a 401", async () => {
    fetchProfileMock.mockRejectedValue(new ApiError("unauthenticated"));

    const { onSessionLost } = renderView();

    await waitFor(() => expect(onSessionLost).toHaveBeenCalled());
  });

  it("signs out through the provided handler", async () => {
    const user = userEvent.setup();
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });

    const { onSignOut } = renderView();
    await screen.findByText("ana@example.com");

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(onSignOut).toHaveBeenCalled();
  });

  it("disables sign-out and communicates the pending state", async () => {
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });

    renderView({ signingOut: true });
    await screen.findByText("ana@example.com");

    expect(screen.getByRole("button", { name: "Signing out…" })).toBeDisabled();
  });

  it("shows the sign-out failure message", async () => {
    fetchProfileMock.mockResolvedValue({
      email: "ana@example.com",
      nickname: "Ana",
    });

    renderView({ signOutFailed: true });
    await screen.findByText("ana@example.com");

    expect(
      screen.getByText("Could not sign out. Please try again."),
    ).toBeInTheDocument();
  });
});

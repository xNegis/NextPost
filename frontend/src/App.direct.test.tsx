import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { createAccount, fetchProfile, fetchSession, signIn } from "./api";
import {
  deleteConsultation,
  fetchConsultationDetail,
  fetchConsultationEntry,
  fetchConsultationPhotoUrl,
  fetchFeed,
  fetchMyConsultation,
  fetchMyConsultationResults,
  fetchMyConsultations,
  fetchMyVote,
} from "./consultationApi";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return {
    ...actual,
    fetchSession: vi.fn(),
    fetchProfile: vi.fn(),
    createAccount: vi.fn(),
    signIn: vi.fn(),
    signOut: vi.fn(),
  };
});

vi.mock("./photoApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./photoApi")>();
  return {
    ...actual,
    fetchApplicationConfig: vi.fn(),
    createUploadSession: vi.fn(),
    renewUploadSession: vi.fn(),
    uploadImage: vi.fn(),
    removeImage: vi.fn(),
    discardUploadSession: vi.fn(),
    fetchImageUrl: vi.fn(),
  };
});

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchConsultationEntry: vi.fn(),
    fetchConsultationCapacity: vi.fn(),
    fetchConsultationDetail: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
    fetchMyVote: vi.fn(),
    fetchMyConsultation: vi.fn(),
    fetchMyConsultationResults: vi.fn(),
    fetchOwnerLink: vi.fn(),
    fetchFeed: vi.fn(),
    fetchMyConsultations: vi.fn(),
    deleteConsultation: vi.fn(),
  };
});

const fetchSessionMock = vi.mocked(fetchSession);
const createAccountMock = vi.mocked(createAccount);
const signInMock = vi.mocked(signIn);
const entryMock = vi.mocked(fetchConsultationEntry);
const ownerDetailMock = vi.mocked(fetchMyConsultation);
const photoMock = vi.mocked(fetchConsultationPhotoUrl);
const resultsMock = vi.mocked(fetchMyConsultationResults);
const detailMock = vi.mocked(fetchConsultationDetail);
const myVoteMock = vi.mocked(fetchMyVote);
const feedMock = vi.mocked(fetchFeed);
const myListMock = vi.mocked(fetchMyConsultations);
const deleteMock = vi.mocked(deleteConsultation);

const CONSULTATION_ID = "123e4567-e89b-12d3-a456-426614174000";
const DIRECT_PATH = `/consultations/${CONSULTATION_ID}`;

const ownerDetail = {
  id: CONSULTATION_ID,
  state: "open" as const,
  owner_nickname: "Ana",
  question: "Which one?",
  context: null,
  audience: "public" as const,
  published_at: "2026-09-28T12:00:00Z",
  photos: [{ id: "photo-1", width: 100, height: 200 }],
};

const readerDetail = {
  id: CONSULTATION_ID,
  owner_nickname: "Ana",
  question: "Which one?",
  context: null,
  audience: "public",
  state: "open",
  published_at: "2026-09-28T12:00:00Z",
  photos: [
    { id: "123e4567-e89b-12d3-a456-426614174001", width: 64, height: 64 },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  fetchSessionMock.mockResolvedValue({ authenticated: false });
  fetchProfileMockSafe();
  photoMock.mockResolvedValue("blob:photo");
  resultsMock.mockResolvedValue({
    consultation_id: CONSULTATION_ID,
    state: "open",
    total_votes: 0,
    options: [{ photo_id: "photo-1", ordinal: 0, vote_count: 0 }],
  });
  myVoteMock.mockResolvedValue({ status: "not_voted" });
  feedMock.mockResolvedValue({ items: [], next_cursor: null });
  myListMock.mockResolvedValue({ items: [], next_cursor: null });
  deleteMock.mockResolvedValue(undefined);
});

function fetchProfileMockSafe() {
  vi.mocked(fetchProfile).mockResolvedValue({
    email: "ana@example.com",
    nickname: "Ana",
  });
}

afterEach(() => {
  window.history.pushState({}, "", "/");
});

function goTo(path: string) {
  window.history.pushState({}, "", path);
}

describe("App direct consultation routing", () => {
  it("shows contextual sign-in copy without any protected request before auth", async () => {
    goTo(DIRECT_PATH);
    render(<App />);

    expect(
      await screen.findByText("Sign in to view this consultation."),
    ).toBeInTheDocument();
    expect(entryMock).not.toHaveBeenCalled();
    expect(detailMock).not.toHaveBeenCalled();
    expect(ownerDetailMock).not.toHaveBeenCalled();
  });

  it("resumes the consultation after a successful sign-in", async () => {
    const user = userEvent.setup();
    goTo(DIRECT_PATH);
    signInMock.mockResolvedValue({ id: "account-1", alias: "Ana" });
    entryMock.mockResolvedValue({ role: "owner" });
    ownerDetailMock.mockResolvedValue(ownerDetail);

    render(<App />);

    await user.type(await screen.findByLabelText("Email"), "ana@example.com");
    await user.type(screen.getByLabelText("Password"), "correct-horse");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(
      await screen.findByRole("heading", { name: "Your consultation" }),
    ).toBeInTheDocument();
    expect(entryMock).toHaveBeenCalledWith(CONSULTATION_ID, null);
  });

  it("preserves a private destination through registration", async () => {
    const user = userEvent.setup();
    const token = `v1.${"A".repeat(43)}`;
    goTo(`${DIRECT_PATH}#access=${token}`);
    createAccountMock.mockResolvedValue({ id: "account-2", alias: "Bea" });
    entryMock.mockResolvedValue({ role: "reader" });
    detailMock.mockResolvedValue(readerDetail);

    render(<App />);

    await user.click(
      await screen.findByRole("button", { name: "Create account" }),
    );
    await user.type(screen.getByLabelText("Email"), "bea@example.com");
    await user.type(screen.getByLabelText("Alias"), "Bea");
    await user.type(screen.getByLabelText("Password"), "correct-horse-123");
    await user.type(
      screen.getByLabelText("Confirm password"),
      "correct-horse-123",
    );
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Ana")).toBeInTheDocument();
    expect(entryMock).toHaveBeenCalledWith(CONSULTATION_ID, token);
    expect(window.location.hash).toBe(`#access=${token}`);
  });

  it("restores an authenticated session directly into the consultation", async () => {
    goTo(DIRECT_PATH);
    fetchSessionMock.mockResolvedValue({
      authenticated: true,
      account: { id: "account-1", alias: "Ana" },
    });
    entryMock.mockResolvedValue({ role: "reader" });
    detailMock.mockResolvedValue(readerDetail);

    render(<App />);

    expect(await screen.findByText("Ana")).toBeInTheDocument();
    expect(entryMock).toHaveBeenCalledWith(CONSULTATION_ID, null);
  });

  it("shows a generic unavailable card for a malformed consultation route", async () => {
    goTo("/consultations/not-a-uuid");
    render(<App />);

    expect(
      await screen.findByText("This consultation is unavailable."),
    ).toBeInTheDocument();
    expect(entryMock).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Go to Home" }),
    ).toBeInTheDocument();
  });

  it("leaves the direct route and renders Home on Go to Home", async () => {
    const user = userEvent.setup();
    goTo(DIRECT_PATH);
    fetchSessionMock.mockResolvedValue({
      authenticated: true,
      account: { id: "account-1", alias: "Ana" },
    });
    entryMock.mockResolvedValue({ role: "reader" });
    detailMock.mockResolvedValue(readerDetail);

    render(<App />);

    await screen.findByText("Ana");
    await user.click(screen.getByRole("button", { name: "Go to Home" }));

    expect(
      await screen.findByRole("heading", { name: "Home" }),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/");
  });

  it("re-enters the direct destination when browser history returns to it", async () => {
    const user = userEvent.setup();
    goTo(DIRECT_PATH);
    fetchSessionMock.mockResolvedValue({
      authenticated: true,
      account: { id: "account-1", alias: "Ana" },
    });
    entryMock.mockResolvedValue({ role: "reader" });
    detailMock.mockResolvedValue(readerDetail);

    render(<App />);
    await screen.findByText("Ana");
    await user.click(screen.getByRole("button", { name: "Go to Home" }));
    await screen.findByRole("heading", { name: "Home" });

    window.history.back();
    window.dispatchEvent(new PopStateEvent("popstate"));

    expect(await screen.findByText("Ana")).toBeInTheDocument();
    expect(entryMock).toHaveBeenCalledTimes(2);
  });

  it("returns to contextual sign-in without losing the URL after session loss", async () => {
    goTo(DIRECT_PATH);
    fetchSessionMock.mockResolvedValue({
      authenticated: true,
      account: { id: "account-1", alias: "Ana" },
    });
    entryMock.mockRejectedValue(
      new (await import("./api")).ApiError("unauthenticated"),
    );

    render(<App />);

    expect(
      await screen.findByText("Sign in to view this consultation."),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe(DIRECT_PATH);
  });

  it("clears the direct route and renders the matching My consultations tab after deletion", async () => {
    const user = userEvent.setup();
    goTo(DIRECT_PATH);
    fetchSessionMock.mockResolvedValue({
      authenticated: true,
      account: { id: "account-1", alias: "Ana" },
    });
    entryMock.mockResolvedValue({ role: "owner" });
    ownerDetailMock.mockResolvedValue(ownerDetail);

    render(<App />);

    await screen.findByRole("heading", { name: "Your consultation" });
    await user.click(
      await screen.findByRole("button", { name: "Delete consultation" }),
    );
    await user.click(
      within(
        screen.getByRole("dialog", { name: "Delete consultation?" }),
      ).getByRole("button", { name: "Delete consultation" }),
    );

    expect(
      await screen.findByRole("heading", { name: "My consultations" }),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/");
    expect(screen.getByText("Consultation deleted")).toBeInTheDocument();
    expect(deleteMock).toHaveBeenCalledWith(CONSULTATION_ID, "open");
  });
});

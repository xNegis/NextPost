import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createUploadSession,
  discardUploadSession,
  fetchApplicationConfig,
  fetchImageUrl,
  uploadImage,
} from "./photoApi";
import { usePhotoUploader } from "./usePhotoUploader";

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

const fetchApplicationConfigMock = vi.mocked(fetchApplicationConfig);
const createUploadSessionMock = vi.mocked(createUploadSession);
const uploadImageMock = vi.mocked(uploadImage);
const discardUploadSessionMock = vi.mocked(discardUploadSession);
const fetchImageUrlMock = vi.mocked(fetchImageUrl);

const defaultConfig = {
  consultation_min_photos: 2,
  consultation_max_photos: 10,
  max_open_consultations: 3,
  photo_max_input_bytes: 15728640,
  consultation_question_max_length: 120,
  consultation_context_max_length: 500,
};

function makeFile(name: string): File {
  return new File([new Uint8Array([1, 2, 3])], name, { type: "image/jpeg" });
}

function Harness() {
  const uploader = usePhotoUploader(() => undefined);
  return (
    <div>
      <span data-testid="session-id">{uploader.sessionId ?? "none"}</span>
      <span data-testid="item-count">{uploader.items.length}</span>
      <button
        type="button"
        onClick={() => uploader.addFiles([makeFile("a.jpg")])}
      >
        add
      </button>
      <button type="button" onClick={() => uploader.relinquish()}>
        relinquish
      </button>
      <button type="button" onClick={() => uploader.setFrozen(true)}>
        freeze
      </button>
    </div>
  );
}

beforeEach(() => {
  fetchApplicationConfigMock.mockResolvedValue(defaultConfig);
  createUploadSessionMock.mockResolvedValue({
    id: "session-1",
    lease_expires_at: "2026-09-28T12:00:00Z",
  });
  uploadImageMock.mockResolvedValue({ id: "image-1", width: 64, height: 64 });
  fetchImageUrlMock.mockResolvedValue("blob:url");
  discardUploadSessionMock.mockResolvedValue(undefined);
});

describe("usePhotoUploader handoff", () => {
  it("exposes the upload-session id to the parent", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("button", { name: "add" }));

    await waitFor(() =>
      expect(screen.getByTestId("session-id")).toHaveTextContent("session-1"),
    );
  });

  it("relinquish clears state without deleting the session", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("button", { name: "add" }));
    await waitFor(() =>
      expect(screen.getByTestId("item-count")).toHaveTextContent("1"),
    );

    await user.click(screen.getByRole("button", { name: "relinquish" }));

    expect(screen.getByTestId("session-id")).toHaveTextContent("none");
    expect(screen.getByTestId("item-count")).toHaveTextContent("0");
    expect(discardUploadSessionMock).not.toHaveBeenCalled();
  });

  it("freeze blocks adding further photos", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("button", { name: "freeze" }));
    await user.click(screen.getByRole("button", { name: "add" }));

    expect(createUploadSessionMock).not.toHaveBeenCalled();
    expect(screen.getByTestId("item-count")).toHaveTextContent("0");
  });
});

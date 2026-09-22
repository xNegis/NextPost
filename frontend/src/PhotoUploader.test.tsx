import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  createUploadSession,
  discardUploadSession,
  fetchApplicationConfig,
  fetchImageUrl,
  removeImage,
  renewUploadSession,
  uploadImage,
} from "./photoApi";
import { PhotoUploader } from "./PhotoUploader";

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
const fetchImageUrlMock = vi.mocked(fetchImageUrl);

function makeFile(name: string): File {
  return new File([new Uint8Array([1, 2, 3])], name, { type: "image/jpeg" });
}

async function waitForPhotoConfig(): Promise<void> {
  await waitFor(() =>
    expect(screen.getByLabelText("Choose photos")).not.toBeDisabled(),
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  fetchApplicationConfigMock.mockResolvedValue({
    consultation_min_photos: 2,
    consultation_max_photos: 10,
    max_open_consultations: 3,
    photo_max_input_bytes: 15728640,
  });
  createUploadSessionMock.mockResolvedValue({
    id: "session-1",
    lease_expires_at: "2026-09-23T12:00:00Z",
  });
  vi.mocked(renewUploadSession).mockResolvedValue({
    id: "session-1",
    lease_expires_at: "2026-09-23T12:00:00Z",
  });
  vi.mocked(removeImage).mockResolvedValue(undefined);
  vi.mocked(discardUploadSession).mockResolvedValue(undefined);
  fetchImageUrlMock.mockResolvedValue("blob:mock-image");
  uploadImageMock.mockResolvedValue({ id: "img-1", width: 64, height: 64 });
});

describe("PhotoUploader", () => {
  it("advertises the accepted image formats on the picker", () => {
    render(<PhotoUploader />);

    const input = screen.getByLabelText("Choose photos");
    expect(input).toHaveAttribute(
      "accept",
      expect.stringContaining("image/heic"),
    );
    expect(input).toHaveAttribute(
      "accept",
      expect.stringContaining("image/webp"),
    );
  });

  it("shows server-driven photo count guidance", async () => {
    render(<PhotoUploader />);

    expect(
      await screen.findByText(
        "Add between 2 and 10 photos for people to compare.",
      ),
    ).toBeInTheDocument();
  });

  it("uploads a photo and reports ordered ready ids", async () => {
    const user = userEvent.setup();
    const onReadyChange = vi.fn();
    render(<PhotoUploader onReadyChange={onReadyChange} />);
    await waitForPhotoConfig();

    await user.upload(
      screen.getByLabelText("Choose photos"),
      makeFile("a.jpg"),
    );

    await waitFor(() => expect(onReadyChange).toHaveBeenCalledWith(["img-1"]));
    expect(
      screen.getByRole("img", { name: "Selected photo 1" }),
    ).toBeInTheDocument();
  });

  it("opens and closes the enlarge dialog with keyboard focus return", async () => {
    const user = userEvent.setup();
    render(<PhotoUploader />);
    await waitForPhotoConfig();

    await user.upload(
      screen.getByLabelText("Choose photos"),
      makeFile("a.jpg"),
    );
    const enlarge = await screen.findByRole("button", { name: "Enlarge" });

    await user.click(enlarge);
    expect(
      screen.getByRole("dialog", { name: "Photo preview" }),
    ).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(
      screen.queryByRole("dialog", { name: "Photo preview" }),
    ).not.toBeInTheDocument();
    expect(enlarge).toHaveFocus();
  });

  it("surfaces a stable upload error with retry and remove actions", async () => {
    const user = userEvent.setup();
    uploadImageMock.mockRejectedValue(new ApiError("unsupported_format"));

    render(<PhotoUploader />);
    await waitForPhotoConfig();
    await user.upload(
      screen.getByLabelText("Choose photos"),
      makeFile("a.bmp"),
    );

    expect(
      await screen.findByText("This file type is not supported."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Try again" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Remove" })).toBeInTheDocument();
  });
});

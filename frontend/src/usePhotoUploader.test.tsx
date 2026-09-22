import { act, render, screen, waitFor } from "@testing-library/react";
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
const renewUploadSessionMock = vi.mocked(renewUploadSession);
const uploadImageMock = vi.mocked(uploadImage);
const removeImageMock = vi.mocked(removeImage);
const discardUploadSessionMock = vi.mocked(discardUploadSession);
const fetchImageUrlMock = vi.mocked(fetchImageUrl);

const defaultConfig = {
  consultation_min_photos: 2,
  consultation_max_photos: 10,
  max_open_consultations: 3,
  photo_max_input_bytes: 15728640,
};

function makeFile(name: string): File {
  return new File([new Uint8Array([1, 2, 3])], name, { type: "image/jpeg" });
}

function Harness({ onSessionLost }: { onSessionLost?: () => void }) {
  const uploader = usePhotoUploader(onSessionLost ?? (() => undefined));
  return (
    <div>
      <button
        type="button"
        onClick={() => uploader.addFiles([makeFile("a.jpg")])}
      >
        add-a
      </button>
      <button
        type="button"
        onClick={() => uploader.addFiles([makeFile("b.jpg")])}
      >
        add-b
      </button>
      <button
        type="button"
        onClick={() =>
          uploader.addFiles([
            makeFile("a.jpg"),
            makeFile("b.jpg"),
            makeFile("c.jpg"),
          ])
        }
      >
        add-three
      </button>
      <button type="button" onClick={() => uploader.discard()}>
        discard
      </button>
      <button
        type="button"
        onClick={() => {
          const first = uploader.items[0];
          if (first) uploader.removeItem(first.clientId);
        }}
      >
        remove-first
      </button>
      <button
        type="button"
        onClick={() => {
          const first = uploader.items[0];
          if (first) uploader.retryItem(first.clientId);
        }}
      >
        retry-first
      </button>
      <output data-testid="ready">{uploader.readyImageIds.join(",")}</output>
      <output data-testid="blocked">{String(uploader.isPublishBlocked)}</output>
      <output data-testid="inactive">{String(uploader.sessionInactive)}</output>
      <output data-testid="config">
        {uploader.config?.consultation_max_photos ?? "loading"}
      </output>
      <ul>
        {uploader.items.map((item) => (
          <li
            key={item.clientId}
            data-testid="item"
            data-status={item.status}
            data-attempt={item.attemptId}
          >
            {item.error ?? item.status}
          </li>
        ))}
      </ul>
    </div>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  fetchApplicationConfigMock.mockResolvedValue(defaultConfig);
  createUploadSessionMock.mockResolvedValue({
    id: "session-1",
    lease_expires_at: "2026-09-23T12:00:00Z",
  });
  renewUploadSessionMock.mockResolvedValue({
    id: "session-1",
    lease_expires_at: "2026-09-23T12:00:00Z",
  });
  discardUploadSessionMock.mockResolvedValue(undefined);
  removeImageMock.mockResolvedValue(undefined);
  fetchImageUrlMock.mockResolvedValue("blob:mock-image");
  uploadImageMock.mockResolvedValue({ id: "img-1", width: 64, height: 64 });
});

describe("usePhotoUploader", () => {
  it("creates a session and uploads a file through to ready", async () => {
    const user = userEvent.setup();
    uploadImageMock.mockImplementation(async () => ({
      id: "img-1",
      width: 64,
      height: 64,
    }));

    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));

    await waitFor(() =>
      expect(screen.getByTestId("ready").textContent).toBe("img-1"),
    );
    expect(createUploadSessionMock).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("blocked").textContent).toBe("false");
  });

  it("transitions through processing before ready", async () => {
    const user = userEvent.setup();
    let bytesSent = () => {};
    let resolveUpload: (value: {
      id: string;
      width: number;
      height: number;
    }) => void = () => {};
    uploadImageMock.mockImplementation(
      (_s, _f, _a, _onProgress, onBytesSent) => {
        bytesSent = onBytesSent;
        return new Promise((resolve) => {
          resolveUpload = resolve;
        });
      },
    );

    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await waitFor(() => expect(screen.getByTestId("item")).toBeInTheDocument());

    await act(async () => {
      bytesSent();
    });
    expect(screen.getByTestId("item").dataset.status).toBe("processing");

    await act(async () => {
      resolveUpload({ id: "img-1", width: 64, height: 64 });
    });
    await waitFor(() =>
      expect(screen.getByTestId("item").dataset.status).toBe("ready"),
    );
  });

  it("maps a stable error and retries with a new attempt id", async () => {
    const user = userEvent.setup();
    const attemptIds: string[] = [];
    uploadImageMock
      .mockImplementationOnce((_s, _f, attemptId) => {
        attemptIds.push(attemptId);
        return Promise.reject(new ApiError("unsupported_format"));
      })
      .mockImplementationOnce((_s, _f, attemptId) => {
        attemptIds.push(attemptId);
        return Promise.resolve({ id: "img-1", width: 64, height: 64 });
      });

    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await waitFor(() =>
      expect(screen.getByTestId("item").dataset.status).toBe("error"),
    );
    expect(screen.getByTestId("item").textContent).toBe(
      "This file type is not supported.",
    );

    await user.click(screen.getByRole("button", { name: "retry-first" }));
    await waitFor(() =>
      expect(screen.getByTestId("item").dataset.status).toBe("ready"),
    );

    expect(attemptIds).toHaveLength(2);
    expect(attemptIds[0]).not.toBe(attemptIds[1]);
  });

  it("keeps the item position when uploading multiple photos", async () => {
    const user = userEvent.setup();
    uploadImageMock.mockImplementation(async (_s, file) => ({
      id: file.name === "a.jpg" ? "img-a" : "img-b",
      width: 64,
      height: 64,
    }));

    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await user.click(screen.getByRole("button", { name: "add-b" }));

    await waitFor(() =>
      expect(screen.getByTestId("ready").textContent).toBe("img-a,img-b"),
    );
  });

  it("does not add more items than the configured maximum", async () => {
    const user = userEvent.setup();
    fetchApplicationConfigMock.mockResolvedValue({
      ...defaultConfig,
      consultation_max_photos: 2,
    });

    render(<Harness />);
    await waitFor(() =>
      expect(screen.getByTestId("config")).toHaveTextContent("2"),
    );
    await user.click(screen.getByRole("button", { name: "add-three" }));

    await waitFor(() => expect(screen.getAllByTestId("item")).toHaveLength(2));
    expect(uploadImageMock).toHaveBeenCalledTimes(2);
  });

  it("removal revokes the server object", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await waitFor(() =>
      expect(screen.getByTestId("item").dataset.status).toBe("ready"),
    );

    await user.click(screen.getByRole("button", { name: "remove-first" }));

    expect(removeImageMock).toHaveBeenCalledWith("session-1", "img-1");
    expect(screen.queryByTestId("item")).not.toBeInTheDocument();
  });

  it("calls onSessionLost on a 401", async () => {
    const user = userEvent.setup();
    const onSessionLost = vi.fn();
    createUploadSessionMock.mockRejectedValue(new ApiError("unauthenticated"));

    render(<Harness onSessionLost={onSessionLost} />);
    await user.click(screen.getByRole("button", { name: "add-a" }));

    await waitFor(() => expect(onSessionLost).toHaveBeenCalled());
  });

  it("clears private photo state when authentication is lost", async () => {
    const user = userEvent.setup();
    const onSessionLost = vi.fn();
    uploadImageMock
      .mockResolvedValueOnce({ id: "img-1", width: 64, height: 64 })
      .mockRejectedValueOnce(new ApiError("unauthenticated"));

    render(<Harness onSessionLost={onSessionLost} />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await waitFor(() =>
      expect(screen.getByTestId("ready")).toHaveTextContent("img-1"),
    );

    await user.click(screen.getByRole("button", { name: "add-b" }));

    await waitFor(() => expect(onSessionLost).toHaveBeenCalled());
    expect(screen.queryByTestId("item")).not.toBeInTheDocument();
    expect(screen.getByTestId("ready")).toHaveTextContent("");
  });

  it("revokes a completed superseded image before a fresh retry", async () => {
    const user = userEvent.setup();
    uploadImageMock
      .mockResolvedValueOnce({ id: "img-old", width: 64, height: 64 })
      .mockResolvedValueOnce({ id: "img-new", width: 64, height: 64 });
    fetchImageUrlMock
      .mockRejectedValueOnce(new ApiError("network"))
      .mockResolvedValueOnce("blob:new-image");

    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await waitFor(() =>
      expect(screen.getByTestId("item")).toHaveAttribute(
        "data-status",
        "error",
      ),
    );

    await user.click(screen.getByRole("button", { name: "retry-first" }));

    await waitFor(() =>
      expect(screen.getByTestId("ready")).toHaveTextContent("img-new"),
    );
    expect(removeImageMock).toHaveBeenCalledWith("session-1", "img-old");
    expect(removeImageMock.mock.invocationCallOrder[0]).toBeLessThan(
      uploadImageMock.mock.invocationCallOrder[1],
    );
  });

  it("clears items when the session becomes inactive", async () => {
    const user = userEvent.setup();
    uploadImageMock.mockRejectedValue(new ApiError("session_inactive"));

    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));

    await waitFor(() =>
      expect(screen.getByTestId("inactive").textContent).toBe("true"),
    );
    expect(screen.queryByTestId("item")).not.toBeInTheDocument();
  });

  it("discards the session on unmount", async () => {
    const user = userEvent.setup();
    const { unmount } = render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await waitFor(() => expect(createUploadSessionMock).toHaveBeenCalled());

    unmount();

    expect(discardUploadSessionMock).toHaveBeenCalledWith("session-1");
  });

  it("revokes object urls on discard", async () => {
    const user = userEvent.setup();
    const revoke = vi.spyOn(URL, "revokeObjectURL");
    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "add-a" }));
    await waitFor(() =>
      expect(screen.getByTestId("item").dataset.status).toBe("ready"),
    );

    await user.click(screen.getByRole("button", { name: "discard" }));

    expect(revoke).toHaveBeenCalledWith("blob:mock-image");
    expect(screen.queryByTestId("item")).not.toBeInTheDocument();
  });

  it("renews the lease on an interval", async () => {
    vi.useFakeTimers();
    try {
      render(<Harness />);
      await act(async () => {
        await vi.runAllTimersAsync();
      });
      await act(async () => {
        screen.getByRole("button", { name: "add-a" }).click();
      });
      await act(async () => {});
      expect(createUploadSessionMock).toHaveBeenCalled();

      await act(async () => {
        vi.advanceTimersByTime(5 * 60 * 1000);
      });

      expect(renewUploadSessionMock).toHaveBeenCalledWith("session-1");
    } finally {
      vi.useRealTimers();
    }
  });
});

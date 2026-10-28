import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import {
  fetchConsultationCapacity,
  fetchConsultationDetail,
  publishConsultation,
} from "./consultationApi";
import { ConsultationComposer } from "./ConsultationComposer";
import {
  createUploadSession,
  discardUploadSession,
  fetchApplicationConfig,
  fetchImageUrl,
  uploadImage,
} from "./photoApi";

vi.mock("./consultationApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./consultationApi")>();
  return {
    ...actual,
    fetchConsultationCapacity: vi.fn(),
    publishConsultation: vi.fn(),
    fetchConsultationDetail: vi.fn(),
    fetchConsultationPhotoUrl: vi.fn(),
    fetchOwnerLink: vi.fn(),
    disableOwnerLink: vi.fn(),
    replaceOwnerLink: vi.fn(),
    createOwnerLink: vi.fn(),
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

const capacityMock = vi.mocked(fetchConsultationCapacity);
const publishMock = vi.mocked(publishConsultation);
const detailMock = vi.mocked(fetchConsultationDetail);
const configMock = vi.mocked(fetchApplicationConfig);
const createSessionMock = vi.mocked(createUploadSession);
const uploadImageMock = vi.mocked(uploadImage);
const fetchImageUrlMock = vi.mocked(fetchImageUrl);
const discardSessionMock = vi.mocked(discardUploadSession);

const config = {
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

function renderComposer(
  props: Partial<React.ComponentProps<typeof ConsultationComposer>> = {},
) {
  return render(
    <ConsultationComposer
      onNavigate={vi.fn()}
      onSessionLost={vi.fn()}
      onDirtyChange={vi.fn()}
      pendingNav={null}
      onCancelNavigation={vi.fn()}
      onViewInMyConsultations={vi.fn()}
      {...props}
    />,
  );
}

async function waitForWizard(): Promise<void> {
  await waitFor(() =>
    expect(
      screen.getByRole("heading", { name: "New consultation" }),
    ).toBeInTheDocument(),
  );
}

async function addTwoPhotos(user: ReturnType<typeof userEvent.setup>) {
  await waitFor(() =>
    expect(screen.getByLabelText("Choose photos")).not.toBeDisabled(),
  );
  await user.upload(screen.getByLabelText("Choose photos"), [
    makeFile("a.jpg"),
    makeFile("b.jpg"),
  ]);
  await waitFor(() =>
    expect(screen.getAllByRole("img", { name: /Selected photo/ })).toHaveLength(
      2,
    ),
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  configMock.mockResolvedValue(config);
  capacityMock.mockResolvedValue({
    open_count: 0,
    limit: 3,
    can_start: true,
  });
  createSessionMock.mockResolvedValue({
    id: "session-1",
    lease_expires_at: "2026-09-28T12:00:00Z",
  });
  uploadImageMock.mockResolvedValue({ id: "img-1", width: 64, height: 64 });
  fetchImageUrlMock.mockResolvedValue("blob:mock");
  discardSessionMock.mockResolvedValue(undefined);
  detailMock.mockResolvedValue({
    id: "consultation-1",
    owner_nickname: "Ana",
    question: "Which one?",
    context: null,
    audience: "public",
    state: "open",
    published_at: "2026-09-28T12:00:00Z",
    photos: [],
  });
});

describe("ConsultationComposer", () => {
  it("shows loading state while configuration and capacity load", () => {
    renderComposer();
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("blocks starting when the author has reached the open-consultation cap", async () => {
    capacityMock.mockResolvedValue({
      open_count: 3,
      limit: 3,
      can_start: false,
    });

    renderComposer();

    expect(
      await screen.findByText(
        "You've reached the limit of 3 open consultations. You can't start another consultation right now.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "View my consultations" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Back Home" }),
    ).toBeInTheDocument();
  });

  it("offers retry when setup loading fails", async () => {
    const user = userEvent.setup();
    configMock.mockRejectedValueOnce(new Error("offline"));

    renderComposer();

    await screen.findByText("Could not load the consultation setup.");
    await user.click(screen.getByRole("button", { name: "Retry" }));

    await waitForWizard();
  });

  it("starts in the Photos step with Continue disabled until photos are ready", async () => {
    renderComposer();
    await waitForWizard();

    expect(screen.getByRole("heading", { name: "Photos" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();
  });

  it("reports dirty and enables Continue once two photos are ready", async () => {
    const user = userEvent.setup();
    const onDirtyChange = vi.fn();
    renderComposer({ onDirtyChange });
    await waitForWizard();

    await addTwoPhotos(user);

    expect(onDirtyChange).toHaveBeenCalledWith(true);
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();
  });

  it("requires an audience before reaching Review", async () => {
    const user = userEvent.setup();
    renderComposer();
    await waitForWizard();
    await addTwoPhotos(user);

    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(
      screen.getByRole("heading", { name: "Details" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByText("Choose an audience.")).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "Public" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(
      screen.getByRole("heading", { name: "Review and publish" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Photo 1 of 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next photo" })).toBeEnabled();
  });

  it("publishes an ordered frozen snapshot", async () => {
    const user = userEvent.setup();
    publishMock.mockResolvedValue({
      id: "consultation-1",
      state: "open",
      audience: "public",
    });

    renderComposer();
    await waitForWizard();
    await addTwoPhotos(user);

    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("radio", { name: "Public" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await user.click(
      screen.getByRole("button", { name: "Publish consultation" }),
    );

    await waitFor(() => expect(publishMock).toHaveBeenCalledTimes(1));
    expect(publishMock).toHaveBeenCalledWith(
      "session-1",
      ["img-1", "img-1"],
      "Which photos should I post?",
      null,
      "public",
    );
  });

  it("relinquishes without discarding and shows the success view", async () => {
    const user = userEvent.setup();
    publishMock.mockResolvedValue({
      id: "consultation-1",
      state: "open",
      audience: "public",
    });

    renderComposer();
    await waitForWizard();
    await addTwoPhotos(user);
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("radio", { name: "Public" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await user.click(
      screen.getByRole("button", { name: "Publish consultation" }),
    );

    expect(await screen.findByText("Published")).toBeInTheDocument();
    expect(discardSessionMock).not.toHaveBeenCalled();
  });

  it("preserves the form and offers retry on a definite publication failure", async () => {
    const user = userEvent.setup();
    publishMock
      .mockRejectedValueOnce(new ApiError("network"))
      .mockResolvedValueOnce({
        id: "consultation-1",
        state: "open",
        audience: "public",
      });

    renderComposer();
    await waitForWizard();
    await addTwoPhotos(user);
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("radio", { name: "Public" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await user.click(
      screen.getByRole("button", { name: "Publish consultation" }),
    );

    expect(
      await screen.findByText(
        "Could not publish. Check your connection and try again.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Review and publish" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(publishMock).toHaveBeenCalledTimes(2));
  });

  it("confirms a dirty Cancel and discards the session on Discard", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    renderComposer({ onNavigate });
    await waitForWizard();
    await addTwoPhotos(user);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(
      await screen.findByRole("dialog", { name: "Discard this consultation?" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Discard" }));

    expect(onNavigate).toHaveBeenCalledWith("home");
    expect(discardSessionMock).toHaveBeenCalledWith("session-1");
  });

  it("keeps editing on a dirty Cancel without discarding", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    renderComposer({ onNavigate });
    await waitForWizard();
    await addTwoPhotos(user);

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await screen.findByRole("dialog", { name: "Discard this consultation?" });

    await user.click(screen.getByRole("button", { name: "Keep editing" }));

    expect(
      screen.queryByRole("dialog", { name: "Discard this consultation?" }),
    ).not.toBeInTheDocument();
    expect(onNavigate).not.toHaveBeenCalled();
  });

  it("blocks navigation during pending publication and completes the handoff safely", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    const onCancelNavigation = vi.fn();
    const onSessionLost = vi.fn();
    const onDirtyChange = vi.fn();
    const onViewInMyConsultations = vi.fn();
    let resolvePublish: (value: unknown) => void = () => undefined;
    publishMock.mockReturnValue(
      new Promise((resolve) => {
        resolvePublish = resolve;
      }),
    );

    const { rerender } = render(
      <ConsultationComposer
        onNavigate={onNavigate}
        onSessionLost={onSessionLost}
        onDirtyChange={onDirtyChange}
        pendingNav={null}
        onCancelNavigation={onCancelNavigation}
        onViewInMyConsultations={onViewInMyConsultations}
      />,
    );
    await waitForWizard();
    await addTwoPhotos(user);
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("radio", { name: "Public" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await user.click(
      screen.getByRole("button", { name: "Publish consultation" }),
    );
    await waitFor(() => expect(publishMock).toHaveBeenCalledTimes(1));
    expect(
      screen.getByRole("button", { name: "Publishing…" }),
    ).toBeInTheDocument();

    rerender(
      <ConsultationComposer
        onNavigate={onNavigate}
        onSessionLost={onSessionLost}
        onDirtyChange={onDirtyChange}
        pendingNav="my"
        onCancelNavigation={onCancelNavigation}
        onViewInMyConsultations={onViewInMyConsultations}
      />,
    );

    await waitFor(() => expect(onCancelNavigation).toHaveBeenCalledTimes(1));
    expect(
      screen.queryByRole("dialog", { name: "Discard this consultation?" }),
    ).not.toBeInTheDocument();
    expect(discardSessionMock).not.toHaveBeenCalled();
    expect(onNavigate).not.toHaveBeenCalled();

    resolvePublish({ id: "consultation-1", state: "open", audience: "public" });

    expect(await screen.findByText("Published")).toBeInTheDocument();
    expect(discardSessionMock).not.toHaveBeenCalled();
  });

  it("delegates session loss when capacity returns 401", async () => {
    const onSessionLost = vi.fn();
    capacityMock.mockRejectedValue(new ApiError("unauthenticated"));
    renderComposer({ onSessionLost });

    await waitFor(() => expect(onSessionLost).toHaveBeenCalledTimes(1));
  });
});

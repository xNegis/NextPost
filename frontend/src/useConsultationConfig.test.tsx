import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api";
import { fetchApplicationConfig } from "./photoApi";
import { useConsultationConfig } from "./useConsultationConfig";

vi.mock("./photoApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./photoApi")>();
  return {
    ...actual,
    fetchApplicationConfig: vi.fn(),
  };
});

const fetchApplicationConfigMock = vi.mocked(fetchApplicationConfig);

const fullConfig = {
  consultation_min_photos: 2,
  consultation_max_photos: 10,
  max_open_consultations: 3,
  photo_max_input_bytes: 15728640,
  consultation_question_max_length: 120,
  consultation_context_max_length: 500,
};

function Harness({ onSessionLost }: { onSessionLost?: () => void }) {
  const result = useConsultationConfig(onSessionLost ?? (() => undefined));
  return (
    <div>
      <output data-testid="status">{result.status}</output>
      <output data-testid="questionMax">
        {result.limits?.questionMax ?? "none"}
      </output>
      <output data-testid="contextMax">
        {result.limits?.contextMax ?? "none"}
      </output>
      <button type="button" onClick={result.retry}>
        retry
      </button>
    </div>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useConsultationConfig", () => {
  it("loads config and exposes text limits", async () => {
    fetchApplicationConfigMock.mockResolvedValue(fullConfig);

    render(<Harness />);

    expect(screen.getByTestId("status").textContent).toBe("loading");
    await waitFor(() =>
      expect(screen.getByTestId("status").textContent).toBe("ready"),
    );
    expect(screen.getByTestId("questionMax").textContent).toBe("120");
    expect(screen.getByTestId("contextMax").textContent).toBe("500");
  });

  it("blocks stale limits during failure and retries", async () => {
    const user = userEvent.setup();
    fetchApplicationConfigMock
      .mockRejectedValueOnce(new ApiError("unavailable"))
      .mockResolvedValueOnce(fullConfig);

    render(<Harness />);

    await waitFor(() =>
      expect(screen.getByTestId("status").textContent).toBe("error"),
    );
    expect(screen.getByTestId("questionMax").textContent).toBe("none");

    await user.click(screen.getByRole("button", { name: "retry" }));

    await waitFor(() =>
      expect(screen.getByTestId("status").textContent).toBe("ready"),
    );
    expect(screen.getByTestId("questionMax").textContent).toBe("120");
  });

  it("delegates 401 to the session-loss callback", async () => {
    const onSessionLost = vi.fn();
    fetchApplicationConfigMock.mockRejectedValue(
      new ApiError("unauthenticated"),
    );

    render(<Harness onSessionLost={onSessionLost} />);

    await waitFor(() => expect(onSessionLost).toHaveBeenCalled());
  });
});

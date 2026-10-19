import { useEffect, useState } from "react";

import { ApiError } from "./api";
import {
  fetchConsultationEntry,
  type ConsultationEntryRole,
} from "./consultationApi";
import type { ConsultationDestination } from "./consultationLink";
import { OwnerConsultationDetail } from "./OwnerConsultationDetail";
import { ReaderConsultationDetail } from "./ReaderConsultationDetail";

interface DirectConsultationEntryProps {
  destination: ConsultationDestination;
  onGoHome: () => void;
  onSessionLost: () => void;
}

type EntryState =
  | { kind: "loading" }
  | { kind: "owner" }
  | { kind: "reader"; role: ConsultationEntryRole }
  | { kind: "unavailable" }
  | { kind: "error" };

export function DirectConsultationEntry({
  destination,
  onGoHome,
  onSessionLost,
}: DirectConsultationEntryProps) {
  const [state, setState] = useState<EntryState>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setState({ kind: "loading" });
    fetchConsultationEntry(destination.consultationId, destination.token)
      .then((entry) => {
        if (!active) return;
        setState(
          entry.role === "owner"
            ? { kind: "owner" }
            : { kind: "reader", role: entry.role },
        );
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.code === "unauthenticated") {
          onSessionLost();
          return;
        }
        if (
          error instanceof ApiError &&
          error.code === "consultation_unavailable"
        ) {
          setState({ kind: "unavailable" });
          return;
        }
        setState({ kind: "error" });
      });
    return () => {
      active = false;
    };
  }, [destination.consultationId, destination.token, attempt, onSessionLost]);

  if (state.kind === "loading") {
    return (
      <section
        className="card direct-entry"
        aria-labelledby="direct-entry-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="direct-entry-title">Consultation</h1>
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Loading consultation…
        </div>
        <button type="button" className="secondary-button" onClick={onGoHome}>
          Go to Home
        </button>
      </section>
    );
  }

  if (state.kind === "owner") {
    return (
      <OwnerConsultationDetail
        consultationId={destination.consultationId}
        variant="direct"
        onBack={onGoHome}
        onSessionLost={onSessionLost}
      />
    );
  }

  if (state.kind === "reader") {
    return (
      <ReaderConsultationDetail
        consultationId={destination.consultationId}
        token={destination.token}
        onBack={onGoHome}
        onSessionLost={onSessionLost}
        exitLabel="Go to Home"
      />
    );
  }

  if (state.kind === "unavailable") {
    return (
      <section
        className="card direct-entry"
        aria-labelledby="direct-entry-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="direct-entry-title">Consultation</h1>
        <div
          className="status status--unavailable"
          role="status"
          aria-live="polite"
        >
          <span className="status__dot" aria-hidden="true" />
          This consultation is unavailable.
        </div>
        <button type="button" className="secondary-button" onClick={onGoHome}>
          Go to Home
        </button>
      </section>
    );
  }

  return (
    <section className="card direct-entry" aria-labelledby="direct-entry-title">
      <p className="eyebrow">NextPost</p>
      <h1 id="direct-entry-title">Consultation</h1>
      <div
        className="status status--unavailable"
        role="status"
        aria-live="polite"
      >
        <span className="status__dot" aria-hidden="true" />
        Could not load this consultation.
      </div>
      <button
        type="button"
        className="primary-button"
        onClick={() => setAttempt((value) => value + 1)}
      >
        Retry
      </button>
      <button type="button" className="secondary-button" onClick={onGoHome}>
        Go to Home
      </button>
    </section>
  );
}

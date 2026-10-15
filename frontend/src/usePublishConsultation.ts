import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import type { Audience } from "./audience";
import { publishConsultation } from "./consultationApi";
import type { ConsultationPublished } from "./consultationApi";

export interface PublishSnapshot {
  sessionId: string;
  orderedImageIds: string[];
  question: string;
  context: string | null;
  audience: Audience;
}

export type PublishStatus = "idle" | "pending" | "success" | "error";

export interface PublishError {
  code: string;
  fieldErrors: Record<string, string>;
  message: string;
}

export interface PublishConsultationResult {
  status: PublishStatus;
  published: ConsultationPublished | null;
  error: PublishError | null;
  publish: (snapshot: PublishSnapshot) => void;
  retry: () => void;
  reset: () => void;
}

export function messageForPublishError(code: string): string {
  switch (code) {
    case "max_open_consultations_reached":
      return "You've reached the limit of open consultations. Close one before publishing another.";
    case "publication_invalid":
      return "This consultation could not be published. Review your photos and try again.";
    case "session_inactive":
      return "Your photo session expired. Please select your photos again.";
    case "consultation_conflict":
      return "This consultation was already published. Refresh to see it.";
    case "unauthenticated":
      return "Your session ended. Please sign in again.";
    case "network":
      return "Could not publish. Check your connection and try again.";
    default:
      return "Could not publish this consultation. Please try again.";
  }
}

export function usePublishConsultation(
  onSessionLost: () => void,
): PublishConsultationResult {
  const [status, setStatus] = useState<PublishStatus>("idle");
  const [published, setPublished] = useState<ConsultationPublished | null>(
    null,
  );
  const [error, setError] = useState<PublishError | null>(null);

  const snapshotRef = useRef<PublishSnapshot | null>(null);
  const pendingRef = useRef(false);
  const onSessionLostRef = useRef(onSessionLost);

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  const submit = useCallback((snapshot: PublishSnapshot) => {
    if (pendingRef.current) return;
    pendingRef.current = true;
    snapshotRef.current = snapshot;
    setStatus("pending");
    setError(null);
    void publishConsultation(
      snapshot.sessionId,
      snapshot.orderedImageIds,
      snapshot.question,
      snapshot.context,
      snapshot.audience,
    )
      .then((result) => {
        pendingRef.current = false;
        setPublished(result);
        setStatus("success");
      })
      .catch((caught: unknown) => {
        pendingRef.current = false;
        const code = caught instanceof ApiError ? caught.code : "unavailable";
        const fieldErrors =
          caught instanceof ApiError ? caught.fieldErrors : {};
        if (code === "unauthenticated") {
          onSessionLostRef.current();
        }
        setError({ code, fieldErrors, message: messageForPublishError(code) });
        setStatus("error");
      });
  }, []);

  const publish = useCallback(
    (snapshot: PublishSnapshot) => submit(snapshot),
    [submit],
  );

  const retry = useCallback(() => {
    const snapshot = snapshotRef.current;
    if (snapshot !== null) submit(snapshot);
  }, [submit]);

  const reset = useCallback(() => {
    snapshotRef.current = null;
    setStatus("idle");
    setPublished(null);
    setError(null);
  }, []);

  return { status, published, error, publish, retry, reset };
}

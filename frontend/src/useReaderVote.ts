import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import { fetchMyVote, submitVote, type VoteStatus } from "./consultationApi";

export type ReaderVoteStatus =
  | { kind: "loading" }
  | { kind: "not_voted" }
  | { kind: "voted"; photoId: string }
  | { kind: "unavailable" }
  | { kind: "error" };

export type SubmitOutcome =
  "idle" | "invalid_selection" | "retryable" | "unknown";

export interface ReaderVoteController {
  status: ReaderVoteStatus;
  submitting: boolean;
  outcome: SubmitOutcome;
  submit: (photoId: string) => Promise<void>;
  retryStatus: () => void;
  checkStatus: () => Promise<void>;
}

export function useReaderVote(
  consultationId: string,
  token: string | null,
  onSessionLost: () => void,
): ReaderVoteController {
  const [status, setStatus] = useState<ReaderVoteStatus>({ kind: "loading" });
  const [submitting, setSubmitting] = useState(false);
  const [outcome, setOutcome] = useState<SubmitOutcome>("idle");

  const generationRef = useRef(0);
  const mountedRef = useRef(true);
  const onSessionLostRef = useRef(onSessionLost);
  const tokenRef = useRef(token);

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const isSessionLost = useCallback(
    (error: unknown): boolean =>
      error instanceof ApiError && error.code === "unauthenticated",
    [],
  );

  const isUnavailable = useCallback(
    (error: unknown): boolean =>
      error instanceof ApiError && error.code === "consultation_unavailable",
    [],
  );

  const applyStatus = useCallback((result: VoteStatus) => {
    if (result.status === "voted") {
      setStatus({ kind: "voted", photoId: result.photo_id });
    } else {
      setStatus({ kind: "not_voted" });
    }
  }, []);

  const checkStatus = useCallback(async (): Promise<void> => {
    const generation = ++generationRef.current;
    setStatus({ kind: "loading" });
    try {
      const result = await fetchMyVote(consultationId, tokenRef.current);
      if (generation !== generationRef.current || !mountedRef.current) return;
      applyStatus(result);
    } catch (error) {
      if (generation !== generationRef.current || !mountedRef.current) return;
      if (isSessionLost(error)) {
        onSessionLostRef.current();
        return;
      }
      if (isUnavailable(error)) {
        setStatus({ kind: "unavailable" });
        return;
      }
      setStatus({ kind: "error" });
    }
  }, [applyStatus, consultationId, isSessionLost, isUnavailable, token]);

  useEffect(() => {
    mountedRef.current = true;
    void checkStatus();
    return () => {
      mountedRef.current = false;
      generationRef.current += 1;
    };
  }, [checkStatus]);

  const retryStatus = useCallback(() => {
    void checkStatus();
  }, [checkStatus]);

  const submit = useCallback(
    async (photoId: string): Promise<void> => {
      const generation = ++generationRef.current;
      setSubmitting(true);
      setOutcome("idle");
      try {
        const result = await submitVote(
          consultationId,
          photoId,
          tokenRef.current,
        );
        if (generation !== generationRef.current || !mountedRef.current) return;
        setStatus({ kind: "voted", photoId: result.photo_id });
      } catch (error) {
        if (generation !== generationRef.current || !mountedRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        if (error instanceof ApiError && error.code === "invalid_selection") {
          setOutcome("invalid_selection");
          return;
        }
        if (isUnavailable(error)) {
          setStatus({ kind: "unavailable" });
          return;
        }
        // A different option already won, or the POST response was lost/ambiguous. Reconcile
        // once against the authoritative status, guarded by this submit's own generation.
        try {
          const current = await fetchMyVote(consultationId, tokenRef.current);
          if (generation !== generationRef.current || !mountedRef.current)
            return;
          if (current.status === "voted") {
            setStatus({ kind: "voted", photoId: current.photo_id });
          } else {
            setOutcome("retryable");
          }
        } catch (reconcileError) {
          if (generation !== generationRef.current || !mountedRef.current)
            return;
          if (isSessionLost(reconcileError)) {
            onSessionLostRef.current();
            return;
          }
          if (isUnavailable(reconcileError)) {
            setStatus({ kind: "unavailable" });
            return;
          }
          setOutcome("unknown");
        }
      } finally {
        if (generation === generationRef.current) setSubmitting(false);
      }
    },
    [consultationId, isSessionLost, isUnavailable],
  );

  return { status, submitting, outcome, submit, retryStatus, checkStatus };
}

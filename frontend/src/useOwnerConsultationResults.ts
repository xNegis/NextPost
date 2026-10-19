import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import {
  fetchMyConsultationResults,
  type ConsultationResult,
} from "./consultationApi";
import { usePeriodicRefresh } from "./usePeriodicRefresh";

export type ResultPhase =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; result: ConsultationResult; stale: boolean }
  | { kind: "error" }
  | { kind: "unavailable" };

export interface OwnerConsultationResultsController {
  phase: ResultPhase;
  retry: () => void;
}

export function useOwnerConsultationResults(
  consultationId: string,
  enabled: boolean,
  onSessionLost: () => void,
): OwnerConsultationResultsController {
  const [phase, setPhase] = useState<ResultPhase>({ kind: "idle" });
  const generationRef = useRef(0);
  const inFlightRef = useRef(false);
  const onSessionLostRef = useRef(onSessionLost);
  const consultationIdRef = useRef(consultationId);

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  useEffect(() => {
    consultationIdRef.current = consultationId;
  }, [consultationId]);

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

  const fetchOnce = useCallback(
    (markLoading: boolean): Promise<void> => {
      if (inFlightRef.current) return Promise.resolve();
      const generation = generationRef.current;
      inFlightRef.current = true;
      if (markLoading) setPhase({ kind: "loading" });
      return fetchMyConsultationResults(consultationIdRef.current)
        .then((result) => {
          if (generation !== generationRef.current) return;
          setPhase({ kind: "ready", result, stale: false });
        })
        .catch((error: unknown) => {
          if (generation !== generationRef.current) return;
          if (isSessionLost(error)) {
            setPhase({ kind: "idle" });
            onSessionLostRef.current();
            return;
          }
          if (isUnavailable(error)) {
            setPhase({ kind: "unavailable" });
            return;
          }
          setPhase((current) =>
            current.kind === "ready"
              ? { ...current, stale: true }
              : { kind: "error" },
          );
        })
        .finally(() => {
          if (generation === generationRef.current) {
            inFlightRef.current = false;
          }
        });
    },
    [isSessionLost, isUnavailable],
  );

  const refresh = useCallback(() => fetchOnce(false), [fetchOnce]);

  usePeriodicRefresh(refresh, enabled && phase.kind !== "unavailable");

  useEffect(() => {
    if (!enabled) {
      generationRef.current += 1;
      inFlightRef.current = false;
      setPhase({ kind: "idle" });
      return;
    }
    generationRef.current += 1;
    inFlightRef.current = false;
    setPhase({ kind: "loading" });
    void fetchOnce(true);
    return () => {
      generationRef.current += 1;
      inFlightRef.current = false;
    };
  }, [enabled, consultationId, fetchOnce]);

  const retry = useCallback(() => {
    void fetchOnce(true);
  }, [fetchOnce]);

  return { phase, retry };
}

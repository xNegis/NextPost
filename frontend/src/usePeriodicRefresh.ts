import { useCallback, useEffect, useRef } from "react";

const DEFAULT_INTERVAL_MS = 5000;

/**
 * Run ``run`` immediately when the document becomes visible again, then every ``intervalMs``
 * after the previous run settles, while ``enabled``. There is at most one run in flight, no
 * queued ticks, and nothing runs while the document is hidden.
 */
export function usePeriodicRefresh(
  run: () => Promise<void>,
  enabled: boolean,
  intervalMs: number = DEFAULT_INTERVAL_MS,
): void {
  const runRef = useRef(run);
  const enabledRef = useRef(enabled);
  const inFlightRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    runRef.current = run;
  }, [run]);

  useEffect(() => {
    enabledRef.current = enabled;
  }, [enabled]);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const schedule = useCallback(() => {
    clearTimer();
    if (!enabledRef.current) return;
    if (
      typeof document === "undefined" ||
      document.visibilityState !== "visible"
    )
      return;
    timerRef.current = setTimeout(() => {
      timerRef.current = null;
      trigger();
    }, intervalMs);
  }, [clearTimer, intervalMs]);

  const trigger = useCallback(() => {
    clearTimer();
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    void runRef
      .current()
      .catch(() => undefined)
      .finally(() => {
        inFlightRef.current = false;
        schedule();
      });
  }, [clearTimer, schedule]);

  useEffect(() => {
    if (!enabled) {
      clearTimer();
      inFlightRef.current = false;
      return;
    }
    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        trigger();
      } else {
        clearTimer();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    schedule();
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      clearTimer();
      inFlightRef.current = false;
    };
  }, [enabled, clearTimer, schedule, trigger]);
}

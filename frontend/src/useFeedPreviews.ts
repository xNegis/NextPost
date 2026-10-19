import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import { fetchConsultationPhotoUrl, type FeedItem } from "./consultationApi";

export type PreviewState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; url: string }
  | { kind: "error" }
  | { kind: "denied" };

const MAX_CONCURRENT_PREVIEWS = 4;

export interface FeedPreviewsController {
  stateFor: (id: string) => PreviewState;
  observe: (id: string, element: HTMLElement | null) => void;
  retry: (id: string) => void;
  revokeAll: () => void;
}

export function useFeedPreviews(
  items: FeedItem[],
  active: boolean,
  onSessionLost: () => void,
): FeedPreviewsController {
  const [states, setStates] = useState<Record<string, PreviewState>>({});

  const itemsRef = useRef<FeedItem[]>(items);
  const activeRef = useRef(active);
  const visibleRef = useRef<Set<string>>(new Set());
  const requestedRef = useRef<Set<string>>(new Set());
  const urlsRef = useRef<Map<string, string>>(new Map());
  const elementsRef = useRef<Map<string, HTMLElement>>(new Map());
  const prevIdsRef = useRef<Set<string> | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const onSessionLostRef = useRef(onSessionLost);
  const drainRef = useRef<() => void>(() => undefined);
  const revokeAllRef = useRef<() => void>(() => undefined);

  // Every request captures an immutable scope plus a per-card request token. A late success,
  // error or 401 is ignored unless it is still the latest request for that card in the same
  // scope, so a stale response can never sign out a later account or replace newer content.
  const scopeRef = useRef(0);
  const tokenSeqRef = useRef(0);
  const inflightTokensRef = useRef<Set<number>>(new Set());
  const latestForCardRef = useRef<Map<string, number>>(new Map());

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  const revokeAll = useCallback(() => {
    for (const url of urlsRef.current.values()) URL.revokeObjectURL(url);
    urlsRef.current.clear();
    requestedRef.current.clear();
    visibleRef.current.clear();
    setStates({});
  }, []);
  revokeAllRef.current = revokeAll;

  const startFetch = useCallback((id: string) => {
    const item = itemsRef.current.find((candidate) => candidate.id === id);
    if (item === undefined) return;
    const scope = scopeRef.current;
    const token = ++tokenSeqRef.current;
    latestForCardRef.current.set(id, token);
    requestedRef.current.add(id);
    inflightTokensRef.current.add(token);
    setStates((current) => ({ ...current, [id]: { kind: "loading" } }));
    void fetchConsultationPhotoUrl(item.id, item.first_photo.id)
      .then((url) => {
        const isCurrent =
          scope === scopeRef.current &&
          latestForCardRef.current.get(id) === token;
        if (!isCurrent || !activeRef.current || !visibleRef.current.has(id)) {
          URL.revokeObjectURL(url);
          return;
        }
        const previous = urlsRef.current.get(id);
        if (previous !== undefined) URL.revokeObjectURL(previous);
        urlsRef.current.set(id, url);
        setStates((current) => ({ ...current, [id]: { kind: "ready", url } }));
      })
      .catch((error: unknown) => {
        const isCurrent =
          scope === scopeRef.current &&
          latestForCardRef.current.get(id) === token;
        if (!isCurrent) return;
        if (error instanceof ApiError && error.code === "unauthenticated") {
          onSessionLostRef.current();
          return;
        }
        if (
          error instanceof ApiError &&
          error.code === "consultation_unavailable"
        ) {
          setStates((current) => ({ ...current, [id]: { kind: "denied" } }));
          return;
        }
        setStates((current) => ({ ...current, [id]: { kind: "error" } }));
      })
      .finally(() => {
        inflightTokensRef.current.delete(token);
        drainRef.current();
      });
  }, []);

  const drain = useCallback(() => {
    if (!activeRef.current) return;
    for (const item of itemsRef.current) {
      if (inflightTokensRef.current.size >= MAX_CONCURRENT_PREVIEWS) break;
      if (!visibleRef.current.has(item.id)) continue;
      if (requestedRef.current.has(item.id)) continue;
      startFetch(item.id);
    }
  }, [startFetch]);
  drainRef.current = drain;

  const getObserver = useCallback(() => {
    if (observerRef.current !== null) return observerRef.current;
    if (typeof IntersectionObserver === "undefined") return null;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = entry.target.getAttribute("data-feed-card");
          if (id === null) continue;
          if (entry.isIntersecting) {
            visibleRef.current.add(id);
          } else if (visibleRef.current.delete(id)) {
            const url = urlsRef.current.get(id);
            if (url !== undefined) {
              URL.revokeObjectURL(url);
              urlsRef.current.delete(id);
            }
            requestedRef.current.delete(id);
            setStates((current) => {
              const next = { ...current };
              next[id] = { kind: "idle" };
              return next;
            });
          }
        }
        drainRef.current();
      },
      { root: null, threshold: 0 },
    );
    observerRef.current = observer;
    return observer;
  }, []);

  const observe = useCallback(
    (id: string, element: HTMLElement | null) => {
      const observer = getObserver();
      if (element === null) {
        const previous = elementsRef.current.get(id);
        if (previous !== undefined) observer?.unobserve(previous);
        elementsRef.current.delete(id);
        visibleRef.current.delete(id);
        const url = urlsRef.current.get(id);
        if (url !== undefined) {
          URL.revokeObjectURL(url);
          urlsRef.current.delete(id);
        }
        requestedRef.current.delete(id);
        setStates((current) => {
          const next = { ...current };
          delete next[id];
          return next;
        });
        return;
      }
      elementsRef.current.set(id, element);
      observer?.observe(element);
    },
    [getObserver],
  );

  const retry = useCallback((id: string) => {
    requestedRef.current.delete(id);
    drainRef.current();
  }, []);

  useEffect(() => {
    activeRef.current = active;
    if (!active) {
      scopeRef.current += 1;
      revokeAll();
    } else {
      drainRef.current();
    }
  }, [active, revokeAll]);

  useEffect(() => {
    itemsRef.current = items;
    const currentIds = new Set(items.map((item) => item.id));
    const previousIds = prevIdsRef.current;
    if (previousIds !== null) {
      for (const previousId of previousIds) {
        if (currentIds.has(previousId)) continue;
        const url = urlsRef.current.get(previousId);
        if (url !== undefined) {
          URL.revokeObjectURL(url);
          urlsRef.current.delete(previousId);
        }
        requestedRef.current.delete(previousId);
        setStates((current) => {
          const next = { ...current };
          delete next[previousId];
          return next;
        });
      }
    }
    prevIdsRef.current = currentIds;
    drainRef.current();
  }, [items]);

  useEffect(() => {
    return () => {
      scopeRef.current += 1;
      observerRef.current?.disconnect();
      revokeAllRef.current();
    };
  }, []);

  const stateFor = useCallback(
    (id: string): PreviewState => states[id] ?? { kind: "idle" },
    [states],
  );

  return { stateFor, observe, retry, revokeAll };
}

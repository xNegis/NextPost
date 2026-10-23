import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import {
  fetchParticipationHistory,
  type ParticipationItem,
} from "./consultationApi";

const PAGE_SIZE = 20;

export type ParticipationStatus = "loading" | "ready" | "error";

export interface ParticipationHistoryController {
  status: ParticipationStatus;
  items: ParticipationItem[];
  nextCursor: string | null;
  loadingMore: boolean;
  loadMoreFailed: boolean;
  loadInitial: () => void;
  loadMore: () => void;
}

export function useParticipationHistory(
  onSessionLost: () => void,
): ParticipationHistoryController {
  const [status, setStatus] = useState<ParticipationStatus>("loading");
  const [items, setItems] = useState<ParticipationItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadMoreFailed, setLoadMoreFailed] = useState(false);

  const generationRef = useRef(0);
  const onSessionLostRef = useRef(onSessionLost);

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  const isSessionLost = useCallback(
    (error: unknown): boolean =>
      error instanceof ApiError && error.code === "unauthenticated",
    [],
  );

  const dedupeAppend = useCallback(
    (existing: ParticipationItem[], next: ParticipationItem[]) => {
      const seen = new Set(existing.map((item) => item.consultation_id));
      return [
        ...existing,
        ...next.filter((item) => {
          if (seen.has(item.consultation_id)) return false;
          seen.add(item.consultation_id);
          return true;
        }),
      ];
    },
    [],
  );

  const loadInitial = useCallback(() => {
    const generation = ++generationRef.current;
    setStatus("loading");
    setItems([]);
    setNextCursor(null);
    setLoadingMore(false);
    setLoadMoreFailed(false);

    void fetchParticipationHistory(PAGE_SIZE, null)
      .then((result) => {
        if (generation !== generationRef.current) return;
        setItems(result.items);
        setNextCursor(result.next_cursor);
        setStatus("ready");
      })
      .catch((error: unknown) => {
        if (generation !== generationRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        setStatus("error");
      });
  }, [isSessionLost]);

  useEffect(() => {
    loadInitial();
  }, [loadInitial]);

  const loadMore = useCallback(() => {
    if (loadingMore || status !== "ready" || nextCursor === null) return;
    const generation = ++generationRef.current;
    setLoadingMore(true);
    setLoadMoreFailed(false);
    void fetchParticipationHistory(PAGE_SIZE, nextCursor)
      .then((result) => {
        if (generation !== generationRef.current) return;
        setItems((current) => dedupeAppend(current, result.items));
        setNextCursor(result.next_cursor);
      })
      .catch((error: unknown) => {
        if (generation !== generationRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        setLoadMoreFailed(true);
      })
      .finally(() => {
        if (generation === generationRef.current) setLoadingMore(false);
      });
  }, [dedupeAppend, isSessionLost, loadingMore, nextCursor, status]);

  useEffect(() => {
    return () => {
      generationRef.current += 1;
    };
  }, []);

  return {
    status,
    items,
    nextCursor,
    loadingMore,
    loadMoreFailed,
    loadInitial,
    loadMore,
  };
}

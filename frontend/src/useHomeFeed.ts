import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import { fetchFeed, type FeedItem } from "./consultationApi";

const PAGE_SIZE = 20;

export type FeedStatus = "loading" | "ready" | "error";

export interface HomeFeedController {
  status: FeedStatus;
  items: FeedItem[];
  nextCursor: string | null;
  refreshing: boolean;
  refreshFailed: boolean;
  loadingMore: boolean;
  loadMoreFailed: boolean;
  loadInitial: () => void;
  refresh: () => Promise<void>;
  reconcile: () => Promise<void>;
  loadMore: () => void;
}

export function useHomeFeed(
  onSessionLost: () => void,
  active = true,
): HomeFeedController {
  const [status, setStatus] = useState<FeedStatus>("loading");
  const [items, setItems] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshFailed, setRefreshFailed] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadMoreFailed, setLoadMoreFailed] = useState(false);

  const generationRef = useRef(0);
  const loadedPagesRef = useRef(0);
  const activeRef = useRef(active);
  const onSessionLostRef = useRef(onSessionLost);

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  const isSessionLost = useCallback(
    (error: unknown): boolean =>
      error instanceof ApiError && error.code === "unauthenticated",
    [],
  );

  const dedupeAppend = useCallback((existing: FeedItem[], next: FeedItem[]) => {
    const seen = new Set(existing.map((item) => item.id));
    return [
      ...existing,
      ...next.filter((item) => {
        if (seen.has(item.id)) return false;
        seen.add(item.id);
        return true;
      }),
    ];
  }, []);

  const loadInitial = useCallback(() => {
    const generation = ++generationRef.current;
    setStatus("loading");
    setItems([]);
    setNextCursor(null);
    setRefreshing(false);
    setLoadingMore(false);
    setLoadMoreFailed(false);
    setRefreshFailed(false);

    void fetchFeed(PAGE_SIZE, null)
      .then((result) => {
        if (generation !== generationRef.current) return;
        setItems(result.items);
        setNextCursor(result.next_cursor);
        loadedPagesRef.current = 1;
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

  const refresh = useCallback((): Promise<void> => {
    if (refreshing || loadingMore || status !== "ready") {
      return Promise.resolve();
    }
    const generation = ++generationRef.current;
    setRefreshing(true);
    setRefreshFailed(false);

    return (async () => {
      try {
        const result = await fetchFeed(PAGE_SIZE, null);
        if (generation !== generationRef.current) return;
        setItems(result.items);
        setNextCursor(result.next_cursor);
        loadedPagesRef.current = 1;
        setStatus("ready");
      } catch (error) {
        if (generation !== generationRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        setRefreshFailed(true);
      } finally {
        if (generation === generationRef.current) setRefreshing(false);
      }
    })();
  }, [isSessionLost, loadingMore, refreshing, status]);

  const reconcile = useCallback((): Promise<void> => {
    if (status === "loading") return Promise.resolve();
    const generation = ++generationRef.current;
    const pages = Math.max(1, loadedPagesRef.current);
    setRefreshing(true);
    setRefreshFailed(false);

    return (async () => {
      try {
        let collected: FeedItem[] = [];
        let cursor: string | null = null;
        let previousCursor: string | null | undefined;
        for (let page = 0; page < pages; page++) {
          const result = await fetchFeed(PAGE_SIZE, cursor);
          if (generation !== generationRef.current) return;
          collected = dedupeAppend(collected, result.items);
          previousCursor = cursor;
          cursor = result.next_cursor;
          if (cursor === null) break;
          if (previousCursor === cursor) break;
        }
        if (generation !== generationRef.current) return;
        setItems(collected);
        setNextCursor(cursor);
        loadedPagesRef.current = pages;
        setStatus("ready");
      } catch (error) {
        if (generation !== generationRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        setRefreshFailed(true);
      } finally {
        if (generation === generationRef.current) setRefreshing(false);
      }
    })();
  }, [dedupeAppend, isSessionLost, status]);

  const loadMore = useCallback(() => {
    if (loadingMore || refreshing || status !== "ready" || nextCursor === null)
      return;
    const generation = ++generationRef.current;
    setLoadingMore(true);
    setLoadMoreFailed(false);
    void fetchFeed(PAGE_SIZE, nextCursor)
      .then((result) => {
        if (generation !== generationRef.current) return;
        setItems((current) => dedupeAppend(current, result.items));
        setNextCursor(result.next_cursor);
        loadedPagesRef.current += 1;
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
  }, [
    dedupeAppend,
    isSessionLost,
    loadingMore,
    nextCursor,
    refreshing,
    status,
  ]);

  useEffect(() => {
    const wasActive = activeRef.current;
    activeRef.current = active;
    if (wasActive && !active) {
      generationRef.current += 1;
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [active]);

  useEffect(() => {
    return () => {
      generationRef.current += 1;
    };
  }, []);

  return {
    status,
    items,
    nextCursor,
    refreshing,
    refreshFailed,
    loadingMore,
    loadMoreFailed,
    loadInitial,
    refresh,
    reconcile,
    loadMore,
  };
}

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { ApiError } from "./api";
import { PRIVATE, PUBLIC } from "./audience";
import {
  fetchMyConsultations,
  type MyConsultationListItem,
  type MyConsultationState,
} from "./consultationApi";
import { formatPublishedDate } from "./consultationDate";
import { OwnerConsultationDetail } from "./OwnerConsultationDetail";
import { usePeriodicRefresh } from "./usePeriodicRefresh";
import { voteCountLabel } from "./voteCount";

const PAGE_SIZE = 20;

type Tab = "open" | "finalized";

const TAB_ORDER: Tab[] = ["open", "finalized"];

type ListStatus = "loading" | "ready" | "error";

interface MyConsultationsProps {
  selectedId: string | null;
  onSelectionChange: (id: string | null) => void;
  onSessionLost: () => void;
  onCreate: () => void;
}

function audienceLabel(audience: string): string {
  return audience === PRIVATE ? "Private" : audience === PUBLIC ? "Public" : "";
}

export function MyConsultations({
  selectedId,
  onSelectionChange,
  onSessionLost,
  onCreate,
}: MyConsultationsProps) {
  const [tab, setTab] = useState<Tab>("open");
  const [items, setItems] = useState<MyConsultationListItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [status, setStatus] = useState<ListStatus>("loading");
  const [refreshing, setRefreshing] = useState(false);
  const [refreshFailed, setRefreshFailed] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadMoreFailed, setLoadMoreFailed] = useState(false);

  const generationRef = useRef(0);
  const loadedPagesRef = useRef(0);
  const onSessionLostRef = useRef(onSessionLost);
  const tabRefs = useRef<Record<Tab, HTMLButtonElement | null>>({
    open: null,
    finalized: null,
  });

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  const isSessionLost = useCallback(
    (error: unknown): boolean =>
      error instanceof ApiError && error.code === "unauthenticated",
    [],
  );

  const dedupeAppend = useCallback(
    (existing: MyConsultationListItem[], next: MyConsultationListItem[]) => {
      const seen = new Set(existing.map((item) => item.id));
      return [
        ...existing,
        ...next.filter((item) => {
          if (seen.has(item.id)) return false;
          seen.add(item.id);
          return true;
        }),
      ];
    },
    [],
  );

  const loadInitial = useCallback(
    (state: MyConsultationState) => {
      const generation = ++generationRef.current;
      setStatus("loading");
      setItems([]);
      setNextCursor(null);
      setRefreshing(false);
      setLoadingMore(false);
      setLoadMoreFailed(false);
      setRefreshFailed(false);

      void fetchMyConsultations(state, PAGE_SIZE, null)
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
    },
    [isSessionLost],
  );

  useEffect(() => {
    loadInitial(tab);
  }, [tab, loadInitial]);

  const refresh = useCallback(async (): Promise<void> => {
    if (refreshing || loadingMore || status !== "ready") return;
    const generation = ++generationRef.current;
    const pages = Math.max(1, loadedPagesRef.current);
    setRefreshing(true);
    setRefreshFailed(false);

    try {
      let collected: MyConsultationListItem[] = [];
      let cursor: string | null = null;
      for (let page = 0; page < pages; page++) {
        const result = await fetchMyConsultations(tab, PAGE_SIZE, cursor);
        if (generation !== generationRef.current) return;
        collected = dedupeAppend(collected, result.items);
        cursor = result.next_cursor;
        if (cursor === null) break;
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
  }, [dedupeAppend, isSessionLost, loadingMore, refreshing, status, tab]);

  const autoRefreshEnabled =
    tab === "open" && selectedId === null && status === "ready";
  usePeriodicRefresh(refresh, autoRefreshEnabled);

  const loadMore = useCallback(() => {
    if (loadingMore || refreshing || status !== "ready" || nextCursor === null)
      return;
    const generation = ++generationRef.current;
    setLoadingMore(true);
    setLoadMoreFailed(false);
    void fetchMyConsultations(tab, PAGE_SIZE, nextCursor)
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
    tab,
  ]);

  const handleBackFromDetail = useCallback(() => {
    onSelectionChange(null);
    if (status === "ready") refresh();
    else loadInitial(tab);
  }, [onSelectionChange, refresh, status, loadInitial, tab]);

  useEffect(() => {
    if (selectedId !== null) {
      generationRef.current += 1;
      setRefreshing(false);
      setLoadingMore(false);
      setRefreshFailed(false);
      setLoadMoreFailed(false);
    }
  }, [selectedId]);

  useEffect(() => {
    return () => {
      generationRef.current += 1;
    };
  }, []);

  const handleTabKeyDown = useCallback(
    (event: KeyboardEvent<HTMLButtonElement>, current: Tab) => {
      const index = TAB_ORDER.indexOf(current);
      let next: Tab | null;
      switch (event.key) {
        case "ArrowRight":
        case "ArrowDown":
          next = TAB_ORDER[(index + 1) % TAB_ORDER.length];
          break;
        case "ArrowLeft":
        case "ArrowUp":
          next = TAB_ORDER[(index - 1 + TAB_ORDER.length) % TAB_ORDER.length];
          break;
        case "Home":
          next = TAB_ORDER[0];
          break;
        case "End":
          next = TAB_ORDER[TAB_ORDER.length - 1];
          break;
        default:
          return;
      }
      event.preventDefault();
      setTab(next);
      tabRefs.current[next]?.focus();
    },
    [],
  );

  if (selectedId !== null) {
    return (
      <OwnerConsultationDetail
        consultationId={selectedId}
        variant="returning"
        onBack={handleBackFromDetail}
        onSessionLost={onSessionLost}
      />
    );
  }

  return (
    <section className="card my-consultations" aria-labelledby="my-title">
      <p className="eyebrow">NextPost</p>
      <h1 id="my-title">My consultations</h1>

      <div
        className="my-consultations__tabs"
        role="tablist"
        aria-label="Consultation state"
      >
        {TAB_ORDER.map((key) => {
          const selected = tab === key;
          const label = key === "open" ? "Open" : "Finalized";
          return (
            <button
              key={key}
              type="button"
              role="tab"
              id={`my-consultations-tab-${key}`}
              aria-selected={selected}
              aria-controls={`my-consultations-panel-${key}`}
              tabIndex={selected ? 0 : -1}
              ref={(element) => {
                tabRefs.current[key] = element;
              }}
              onClick={() => setTab(key)}
              onKeyDown={(event) => handleTabKeyDown(event, key)}
            >
              {label}
            </button>
          );
        })}
      </div>

      <div
        role="tabpanel"
        id={`my-consultations-panel-${tab}`}
        aria-labelledby={`my-consultations-tab-${tab}`}
        tabIndex={0}
      >
        {status === "loading" && (
          <div className="status" role="status" aria-live="polite">
            <span className="status__dot" aria-hidden="true" />
            Loading your consultations…
          </div>
        )}

        {status === "error" && (
          <>
            <div
              className="status status--unavailable"
              role="status"
              aria-live="polite"
            >
              <span className="status__dot" aria-hidden="true" />
              Could not load your consultations.
            </div>
            <button
              type="button"
              className="primary-button"
              onClick={() => loadInitial(tab)}
            >
              Retry
            </button>
          </>
        )}

        {status === "ready" && items.length === 0 && (
          <div className="my-consultations__empty">
            {tab === "open" ? (
              <>
                <p>You have no open consultations.</p>
                <button
                  type="button"
                  className="primary-button"
                  onClick={onCreate}
                >
                  Create consultation
                </button>
              </>
            ) : (
              <p>You have no finalized consultations.</p>
            )}
          </div>
        )}

        {status === "ready" && items.length > 0 && (
          <>
            <ul className="my-consultations__list">
              {items.map((item) => (
                <li key={item.id} className="my-consultations__row">
                  {item.state === "open" ? (
                    <>
                      <p className="my-consultations__question" dir="auto">
                        {item.question}
                      </p>
                      <p className="my-consultations__facts">
                        {audienceLabel(item.audience)} · Open · Published{" "}
                        <time dateTime={item.published_at}>
                          {formatPublishedDate(item.published_at)}
                        </time>
                      </p>
                      <p className="my-consultations__votes">
                        {voteCountLabel(item.total_votes)}
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="my-consultations__question">
                        Consultation {item.id}
                      </p>
                      <p className="my-consultations__facts">
                        Finalized · Published{" "}
                        <time dateTime={item.published_at}>
                          {formatPublishedDate(item.published_at)}
                        </time>
                      </p>
                    </>
                  )}
                  <button
                    type="button"
                    className="secondary-button my-consultations__view"
                    onClick={() => onSelectionChange(item.id)}
                  >
                    View consultation
                  </button>
                </li>
              ))}
            </ul>

            {loadMoreFailed ? (
              <button
                type="button"
                className="secondary-button"
                onClick={loadMore}
              >
                Try loading more
              </button>
            ) : (
              nextCursor !== null && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={loadMore}
                  disabled={loadingMore || refreshing}
                >
                  {loadingMore ? "Loading…" : "Load more"}
                </button>
              )
            )}
          </>
        )}

        {status === "ready" && refreshFailed && (
          <p className="field-error" role="alert">
            {items.length > 0
              ? "Could not refresh. Showing your earlier consultations."
              : "Could not refresh your consultations."}
          </p>
        )}

        {status === "ready" && (
          <button
            type="button"
            className="secondary-button"
            onClick={refresh}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        )}
      </div>
    </section>
  );
}

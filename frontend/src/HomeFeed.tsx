import { useCallback, useEffect, useRef, useState } from "react";

import type { FeedItem, MyConsultationState } from "./consultationApi";
import { FeedCard } from "./FeedCard";
import { OwnerConsultationDetail } from "./OwnerConsultationDetail";
import { ReaderConsultationDetail } from "./ReaderConsultationDetail";
import { useFeedPreviews } from "./useFeedPreviews";
import { useHomeFeed } from "./useHomeFeed";

interface HomeFeedProps {
  onSessionLost: () => void;
  onDeleted?: (state: MyConsultationState) => void;
}

export function HomeFeed({ onSessionLost, onDeleted }: HomeFeedProps) {
  const [selected, setSelected] = useState<FeedItem | null>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const pendingFocusRef = useRef<string | null>(null);

  const {
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
  } = useHomeFeed(onSessionLost, selected === null);

  const previews = useFeedPreviews(items, selected === null, onSessionLost);

  const handleView = useCallback((item: FeedItem) => {
    setSelected(item);
  }, []);

  const handleBackFromDetail = useCallback(() => {
    pendingFocusRef.current = selected?.id ?? null;
    setSelected(null);
    if (status === "ready") {
      void reconcile();
    } else {
      loadInitial();
    }
  }, [selected, status, reconcile, loadInitial]);

  useEffect(() => {
    if (selected !== null || refreshing) return;
    const targetId = pendingFocusRef.current;
    if (targetId !== null) {
      const target = document.getElementById(`feed-view-${targetId}`);
      (target ?? headingRef.current)?.focus();
    }
    pendingFocusRef.current = null;
  }, [items, refreshing, selected]);

  if (selected !== null) {
    if (selected.is_owner) {
      return (
        <OwnerConsultationDetail
          consultationId={selected.id}
          variant="home"
          onBack={handleBackFromDetail}
          onDeleted={onDeleted}
          onSessionLost={onSessionLost}
        />
      );
    }
    return (
      <ReaderConsultationDetail
        consultationId={selected.id}
        onBack={handleBackFromDetail}
        onSessionLost={onSessionLost}
      />
    );
  }

  return (
    <section className="card home-feed" aria-labelledby="home-title">
      <p className="eyebrow">NextPost</p>
      <h1 id="home-title" tabIndex={-1} ref={headingRef}>
        Home
      </h1>
      <p className="summary">
        Browse open public consultations and read the purpose behind each
        comparison.
      </p>

      {status === "loading" && (
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Loading consultations…
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
            Could not load consultations.
          </div>
          <button
            type="button"
            className="primary-button"
            onClick={loadInitial}
          >
            Retry
          </button>
        </>
      )}

      {status === "ready" && items.length === 0 && (
        <div className="home-feed__empty">
          <p>No open public consultations yet.</p>
          {refreshFailed && (
            <p className="field-error" role="alert">
              Could not refresh. Showing earlier consultations.
            </p>
          )}
          <button
            type="button"
            className="secondary-button"
            onClick={() => void refresh()}
            disabled={refreshing}
          >
            Refresh
          </button>
        </div>
      )}

      {status === "ready" && items.length > 0 && (
        <>
          <ul className="home-feed__list">
            {items.map((item) => (
              <FeedCard
                key={item.id}
                item={item}
                preview={previews.stateFor(item.id)}
                observe={previews.observe}
                retry={previews.retry}
                onView={() => handleView(item)}
              />
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

          {refreshFailed && (
            <p className="field-error" role="alert">
              Could not refresh. Showing earlier consultations.
            </p>
          )}

          <button
            type="button"
            className="secondary-button"
            onClick={() => void refresh()}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        </>
      )}
    </section>
  );
}

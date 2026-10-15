import { useCallback } from "react";

import { formatPublishedDate } from "./consultationDate";
import type { FeedItem } from "./consultationApi";
import type { PreviewState } from "./useFeedPreviews";

interface FeedCardProps {
  item: FeedItem;
  preview: PreviewState;
  observe: (id: string, element: HTMLElement | null) => void;
  retry: (id: string) => void;
  onView: () => void;
}

export function FeedCard({
  item,
  preview,
  observe,
  retry,
  onView,
}: FeedCardProps) {
  const observeRef = useCallback(
    (element: HTMLElement | null) => observe(item.id, element),
    [observe, item.id],
  );

  if (preview.kind === "denied") {
    return (
      <li
        className="feed-card feed-card--denied"
        data-feed-card={item.id}
        ref={observeRef}
      >
        <p className="feed-card__unavailable">
          This consultation is unavailable.
        </p>
      </li>
    );
  }

  return (
    <li className="feed-card" data-feed-card={item.id} ref={observeRef}>
      <h2 className="feed-card__question" dir="auto">
        {item.question}
      </h2>
      <p className="feed-card__nickname" dir="auto">
        {item.owner_nickname}
      </p>
      <p className="feed-card__facts">
        Public · Open · Published{" "}
        <time dateTime={item.published_at}>
          {formatPublishedDate(item.published_at)}
        </time>
      </p>
      {item.is_owner && (
        <span className="feed-card__own">Your consultation</span>
      )}
      {item.context_excerpt !== null && (
        <p className="feed-card__excerpt" dir="auto">
          {item.context_excerpt}
        </p>
      )}

      <div className="feed-card__preview">
        <span className="feed-card__photo-label">Photo 1</span>
        {preview.kind === "idle" && (
          <div
            className="feed-card__photo feed-card__photo--idle"
            aria-hidden="true"
          />
        )}
        {preview.kind === "loading" && (
          <div
            className="status feed-card__photo-status"
            role="status"
            aria-live="polite"
          >
            <span className="status__dot" aria-hidden="true" />
            Loading photo…
          </div>
        )}
        {preview.kind === "ready" && (
          <img className="feed-card__photo" src={preview.url} alt="Photo 1" />
        )}
        {preview.kind === "error" && (
          <div className="feed-card__photo-error" role="alert">
            <p>Could not load the photo.</p>
            <button
              type="button"
              className="secondary-button feed-card__photo-retry"
              onClick={() => retry(item.id)}
            >
              Retry photo
            </button>
          </div>
        )}
      </div>

      <button
        type="button"
        className="secondary-button feed-card__view"
        id={`feed-view-${item.id}`}
        onClick={onView}
      >
        View consultation
      </button>
    </li>
  );
}

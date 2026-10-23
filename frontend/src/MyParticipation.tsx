import type { ParticipationItem } from "./consultationApi";
import { formatPublishedDate } from "./consultationDate";
import { useParticipationHistory } from "./useParticipationHistory";

interface MyParticipationProps {
  onSessionLost: () => void;
  onViewConsultation: (consultationId: string) => void;
  onGoHome: () => void;
}

const STATUS_LABELS: Record<ParticipationItem["status"], string> = {
  open: "Open",
  matched: "Matched",
  not_matched: "Not matched",
  no_choice: "No choice",
  unavailable: "Unavailable",
};

function eventLabel(item: ParticipationItem): string {
  const date = formatPublishedDate(item.event_at);
  return item.event_kind === "voted" ? `Voted ${date}` : `Finalized ${date}`;
}

export function MyParticipation({
  onSessionLost,
  onViewConsultation,
  onGoHome,
}: MyParticipationProps) {
  const {
    status,
    items,
    nextCursor,
    loadingMore,
    loadMoreFailed,
    loadInitial,
    loadMore,
  } = useParticipationHistory(onSessionLost);

  return (
    <section
      className="card my-participation"
      aria-labelledby="participation-title"
    >
      <p className="eyebrow">NextPost</p>
      <h1 id="participation-title">My participation</h1>

      <p className="my-participation__help">
        Matching compares your vote with the author&apos;s declared choice. It
        is not a score.
      </p>

      {status === "loading" && (
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Loading your participation…
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
            Could not load your participation.
          </div>
          <button
            type="button"
            className="primary-button"
            onClick={() => loadInitial()}
          >
            Retry
          </button>
        </>
      )}

      {status === "ready" && items.length === 0 && (
        <div className="my-participation__empty">
          <p>Consultations you vote in will appear here.</p>
          <button type="button" className="primary-button" onClick={onGoHome}>
            Go to Home
          </button>
        </div>
      )}

      {status === "ready" && items.length > 0 && (
        <>
          <ul className="my-participation__list">
            {items.map((item) => (
              <li key={item.consultation_id} className="my-participation__row">
                <p className="my-participation__reference">
                  Consultation {item.consultation_id}
                </p>
                <p className="my-participation__status">
                  {STATUS_LABELS[item.status]}
                </p>
                <p className="my-participation__facts">
                  <time dateTime={item.event_at}>{eventLabel(item)}</time>
                  {item.status === "no_choice" && (
                    <span className="my-participation__no-choice">
                      {" "}
                      · The author declared no selected photo.
                    </span>
                  )}
                </p>
                {item.can_view && (
                  <button
                    type="button"
                    className="secondary-button my-participation__view"
                    onClick={() => onViewConsultation(item.consultation_id)}
                  >
                    View consultation
                  </button>
                )}
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
                disabled={loadingMore}
              >
                {loadingMore ? "Loading…" : "Load more"}
              </button>
            )
          )}
        </>
      )}
    </section>
  );
}

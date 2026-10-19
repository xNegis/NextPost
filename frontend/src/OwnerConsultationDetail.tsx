import { PRIVATE } from "./audience";
import { ConsultationTextDisplay } from "./ConsultationTextDisplay";
import { buildConsultationUrl } from "./consultationLink";
import { formatPublishedDate } from "./consultationDate";
import { PrivateLinkControls } from "./PrivateLinkControls";
import { ShareConsultation } from "./ShareConsultation";
import { useOwnerConsultationDetail } from "./useOwnerConsultationDetail";
import { useOwnerConsultationResults } from "./useOwnerConsultationResults";
import { voteCountLabel } from "./voteCount";

interface OwnerConsultationDetailProps {
  consultationId: string;
  variant: "success" | "returning" | "home" | "direct";
  onBack: () => void;
  onViewInMyConsultations?: () => void;
  onSessionLost: () => void;
}

const backLabel = (variant: "success" | "returning" | "home" | "direct") =>
  variant === "success"
    ? "Back Home"
    : variant === "home"
      ? "Back to Home"
      : variant === "direct"
        ? "Go to Home"
        : "Back to My consultations";

function buildPrivateLink(
  consultationId: string,
  token: string | null | undefined,
): string | null {
  if (token === null || token === undefined) return null;
  try {
    return buildConsultationUrl(window.location.origin, consultationId, token);
  } catch {
    return null;
  }
}

function buildPublicLink(consultationId: string): string | null {
  try {
    return buildConsultationUrl(window.location.origin, consultationId);
  } catch {
    return null;
  }
}

export function OwnerConsultationDetail({
  consultationId,
  variant,
  onBack,
  onViewInMyConsultations,
  onSessionLost,
}: OwnerConsultationDetailProps) {
  const {
    phase,
    link,
    linkPending,
    retry,
    disable,
    replace,
    createNew,
    refreshLink,
  } = useOwnerConsultationDetail(consultationId, onSessionLost);

  const results = useOwnerConsultationResults(
    consultationId,
    phase.kind === "open",
    onSessionLost,
  );

  const heading = variant === "success" ? "Published" : "Your consultation";
  const back = backLabel(variant);

  if (phase.kind === "loading") {
    return (
      <section
        className="card owner-consultation"
        aria-labelledby="owner-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="owner-title">{heading}</h1>
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Loading your consultation…
        </div>
      </section>
    );
  }

  if (phase.kind === "error") {
    return (
      <section
        className="card owner-consultation"
        aria-labelledby="owner-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="owner-title">{heading}</h1>
        <div
          className="status status--unavailable"
          role="status"
          aria-live="polite"
        >
          <span className="status__dot" aria-hidden="true" />
          Could not load your consultation.
        </div>
        <button type="button" className="primary-button" onClick={retry}>
          Retry
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          {back}
        </button>
      </section>
    );
  }

  if (phase.kind === "unavailable") {
    return (
      <section
        className="card owner-consultation"
        aria-labelledby="owner-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="owner-title">{heading}</h1>
        <div
          className="status status--unavailable"
          role="status"
          aria-live="polite"
        >
          <span className="status__dot" aria-hidden="true" />
          This consultation is unavailable.
        </div>
        {phase.refreshable && (
          <button type="button" className="primary-button" onClick={retry}>
            Refresh
          </button>
        )}
        <button type="button" className="secondary-button" onClick={onBack}>
          {back}
        </button>
      </section>
    );
  }

  if (phase.kind === "finalized") {
    return (
      <section
        className="card owner-consultation"
        aria-labelledby="owner-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="owner-title">{heading}</h1>
        <p className="summary">Photos are no longer available.</p>
        <dl className="owner-consultation__meta-list">
          <div className="owner-consultation__meta-row">
            <dt>Reference</dt>
            <dd>{phase.detail.id}</dd>
          </div>
          <div className="owner-consultation__meta-row">
            <dt>State</dt>
            <dd>Finalized</dd>
          </div>
          <div className="owner-consultation__meta-row">
            <dt>Published</dt>
            <dd>
              <time dateTime={phase.detail.published_at}>
                {formatPublishedDate(phase.detail.published_at)}
              </time>
            </dd>
          </div>
        </dl>
        <button type="button" className="primary-button" onClick={retry}>
          Refresh
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          {back}
        </button>
      </section>
    );
  }

  const isPrivate = phase.detail.audience === PRIVATE;
  const readyLink = link.kind === "ready" ? link.link : null;
  const privateLink = buildPrivateLink(consultationId, readyLink?.token);
  const publicLink = buildPublicLink(consultationId);
  const shareLink = isPrivate
    ? readyLink?.active
      ? privateLink
      : null
    : publicLink;

  return (
    <section className="card owner-consultation" aria-labelledby="owner-title">
      <p className="eyebrow">NextPost</p>
      <h1 id="owner-title">{heading}</h1>
      {variant === "success" && (
        <p className="summary">Your consultation is now live.</p>
      )}

      <div className="status owner-consultation__status" role="status">
        <span className="status__dot" aria-hidden="true" />
        Open
      </div>

      <p className="owner-consultation__meta">
        Published{" "}
        <time dateTime={phase.detail.published_at}>
          {formatPublishedDate(phase.detail.published_at)}
        </time>
      </p>
      <p className="owner-consultation__reach">
        {isPrivate
          ? "Private: only people with the link and an account can see this consultation."
          : "Public: anyone with an account can find and see this consultation."}
      </p>

      <ConsultationTextDisplay
        question={phase.detail.question}
        context={phase.detail.context}
        headingLevel={2}
      />

      {phase.photoUrls.length > 0 && (
        <ul className="owner-consultation__photos">
          {phase.photoUrls.map((url, index) => {
            const photoId = phase.detail.photos[index]?.id;
            const count =
              results.phase.kind === "ready" && photoId !== undefined
                ? results.phase.result.options.find(
                    (option) => option.photo_id === photoId,
                  )?.vote_count
                : undefined;
            return (
              <li key={url} className="owner-consultation__photo">
                <img src={url} alt={`Consultation photo ${index + 1}`} />
                {count !== undefined && (
                  <p
                    className="owner-consultation__photo-count"
                    aria-label={`Photo ${index + 1}: ${voteCountLabel(count)}`}
                  >
                    {voteCountLabel(count)}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <section
        className="owner-consultation__results"
        aria-labelledby="owner-results-title"
      >
        <h2 id="owner-results-title">Results</h2>
        {results.phase.kind === "loading" && (
          <div className="status" role="status" aria-live="polite">
            <span className="status__dot" aria-hidden="true" />
            Loading results…
          </div>
        )}
        {results.phase.kind === "error" && (
          <>
            <div
              className="status status--unavailable"
              role="status"
              aria-live="polite"
            >
              <span className="status__dot" aria-hidden="true" />
              Could not load results.
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={results.retry}
            >
              Retry
            </button>
          </>
        )}
        {results.phase.kind === "unavailable" && (
          <>
            <div
              className="status status--unavailable"
              role="status"
              aria-live="polite"
            >
              <span className="status__dot" aria-hidden="true" />
              Results are unavailable. Refresh the consultation to check its
              current state.
            </div>
            <button type="button" className="secondary-button" onClick={retry}>
              Refresh consultation
            </button>
          </>
        )}
        {results.phase.kind === "ready" && (
          <>
            <p className="owner-consultation__results-total">
              {voteCountLabel(results.phase.result.total_votes)}
            </p>
            <p className="owner-consultation__results-note">
              These are participant opinions and may change while your
              consultation is open.
            </p>
            {results.phase.stale && (
              <p className="field-error" role="alert">
                Results could not be refreshed. Showing earlier counts.
              </p>
            )}
          </>
        )}
      </section>

      <section
        className="owner-consultation__share"
        aria-labelledby="owner-share-title"
      >
        <h2 id="owner-share-title">Share consultation</h2>
        <ShareConsultation link={shareLink} />
      </section>

      {isPrivate && (
        <div className="owner-consultation__link">
          {link.kind === "loading" && (
            <div className="status" role="status" aria-live="polite">
              <span className="status__dot" aria-hidden="true" />
              Loading private link…
            </div>
          )}
          {link.kind === "error" && (
            <div className="private-link-controls__error" role="alert">
              <p>{link.message}</p>
              <button
                type="button"
                className="secondary-button"
                onClick={refreshLink}
              >
                Try again
              </button>
            </div>
          )}
          {link.kind === "stale" && (
            <div className="private-link-controls__error" role="alert">
              <p>{link.message}</p>
              <button
                type="button"
                className="secondary-button"
                onClick={refreshLink}
              >
                Refresh link
              </button>
            </div>
          )}
          {link.kind === "ready" && (
            <PrivateLinkControls
              status={readyLink?.active ? "active" : "disabled"}
              pending={linkPending}
              onDisable={disable}
              onReplace={replace}
              onCreateNew={createNew}
              onRefresh={refreshLink}
            />
          )}
        </div>
      )}

      <div className="owner-consultation__actions">
        {variant === "success" && onViewInMyConsultations && (
          <button
            type="button"
            className="primary-button"
            onClick={onViewInMyConsultations}
          >
            View in My consultations
          </button>
        )}
        <button type="button" className="secondary-button" onClick={retry}>
          Refresh
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          {back}
        </button>
      </div>
    </section>
  );
}

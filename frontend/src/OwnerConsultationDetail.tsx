import { PRIVATE } from "./audience";
import { ConsultationTextDisplay } from "./ConsultationTextDisplay";
import { buildConsultationUrl } from "./consultationLink";
import { formatPublishedDate } from "./consultationDate";
import { PrivateLinkControls } from "./PrivateLinkControls";
import { useOwnerConsultationDetail } from "./useOwnerConsultationDetail";

interface OwnerConsultationDetailProps {
  consultationId: string;
  variant: "success" | "returning" | "home";
  onBack: () => void;
  onViewInMyConsultations?: () => void;
  onSessionLost: () => void;
}

const backLabel = (variant: "success" | "returning" | "home") =>
  variant === "success"
    ? "Back Home"
    : variant === "home"
      ? "Back to Home"
      : "Back to My consultations";

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
    copyFailed,
    retry,
    copy,
    disable,
    replace,
    createNew,
    refreshLink,
  } = useOwnerConsultationDetail(consultationId, onSessionLost);

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
          {phase.photoUrls.map((url, index) => (
            <li key={url} className="owner-consultation__photo">
              <img src={url} alt={`Consultation photo ${index + 1}`} />
            </li>
          ))}
        </ul>
      )}

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
            <>
              <PrivateLinkControls
                status={readyLink?.active ? "active" : "disabled"}
                link={
                  readyLink?.token !== null && readyLink?.token !== undefined
                    ? buildConsultationUrl(
                        window.location.origin,
                        consultationId,
                        readyLink.token,
                      )
                    : null
                }
                pending={linkPending}
                onCopy={copy}
                onDisable={disable}
                onReplace={replace}
                onCreateNew={createNew}
                onRefresh={refreshLink}
              />
              <p className="owner-consultation__link-note">
                Opening shared links is not available yet.
              </p>
              {copyFailed && (
                <p className="field-error" role="alert">
                  Could not copy the link. Copy it manually.
                </p>
              )}
            </>
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

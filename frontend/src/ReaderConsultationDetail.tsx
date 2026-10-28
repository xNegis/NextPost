import { useState } from "react";

import { ConsultationTextDisplay } from "./ConsultationTextDisplay";
import { formatPublishedDate } from "./consultationDate";
import { PhotoEnlargement } from "./PhotoEnlargement";
import { useReaderConsultationDetail } from "./useReaderConsultationDetail";
import { useReaderVote } from "./useReaderVote";

interface ReaderConsultationDetailProps {
  consultationId: string;
  onBack: () => void;
  onSessionLost: () => void;
  token?: string | null;
  exitLabel?: string;
}

interface EnlargedPhoto {
  src: string;
  alt: string;
}

export function ReaderConsultationDetail({
  consultationId,
  onBack,
  onSessionLost,
  token = null,
  exitLabel = "Back to Home",
}: ReaderConsultationDetailProps) {
  const { phase, retry } = useReaderConsultationDetail(
    consultationId,
    onSessionLost,
    token,
  );
  const vote = useReaderVote(consultationId, token, onSessionLost);
  const [enlarged, setEnlarged] = useState<EnlargedPhoto | null>(null);
  const [selectedPhotoId, setSelectedPhotoId] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState(false);
  const retryProtectedState = () => {
    retry();
    vote.retryStatus();
  };

  if (phase.kind === "loading") {
    return (
      <section
        className="card reader-consultation"
        aria-labelledby="reader-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="reader-title">Consultation</h1>
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Loading consultation…
        </div>
        <button type="button" className="secondary-button" onClick={onBack}>
          {exitLabel}
        </button>
      </section>
    );
  }

  if (phase.kind === "unavailable" || vote.status.kind === "unavailable") {
    return (
      <section
        className="card reader-consultation"
        aria-labelledby="reader-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="reader-title">Consultation</h1>
        <div
          className="status status--unavailable"
          role="status"
          aria-live="polite"
        >
          <span className="status__dot" aria-hidden="true" />
          This consultation is unavailable.
        </div>
        <button
          type="button"
          className="primary-button"
          onClick={retryProtectedState}
        >
          Refresh
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          {exitLabel}
        </button>
      </section>
    );
  }

  if (phase.kind === "error") {
    return (
      <section
        className="card reader-consultation"
        aria-labelledby="reader-title"
      >
        <p className="eyebrow">NextPost</p>
        <h1 id="reader-title">Consultation</h1>
        <div
          className="status status--unavailable"
          role="status"
          aria-live="polite"
        >
          <span className="status__dot" aria-hidden="true" />
          Could not load this consultation.
        </div>
        <button type="button" className="primary-button" onClick={retry}>
          Retry
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          {exitLabel}
        </button>
      </section>
    );
  }

  const audienceLabel =
    phase.detail.audience === "private" ? "Private" : "Public";
  const selectedIndex =
    selectedPhotoId === null
      ? -1
      : phase.detail.photos.findIndex((photo) => photo.id === selectedPhotoId);
  const votedPhotoId =
    vote.status.kind === "voted" ? vote.status.photoId : null;

  return (
    <section
      className="card reader-consultation"
      aria-labelledby="reader-title"
    >
      <p className="eyebrow">NextPost</p>
      <h1 id="reader-title">Consultation</h1>

      <p className="reader-consultation__nickname" dir="auto">
        {phase.detail.owner_nickname}
      </p>
      <p className="reader-consultation__facts">
        {audienceLabel} · Open · Published{" "}
        <time dateTime={phase.detail.published_at}>
          {formatPublishedDate(phase.detail.published_at)}
        </time>
      </p>

      <ConsultationTextDisplay
        question={phase.detail.question}
        context={phase.detail.context}
        headingLevel={2}
      />

      {vote.status.kind === "loading" && (
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Checking your vote…
        </div>
      )}

      {vote.status.kind === "error" && (
        <div className="reader-consultation__vote-status" role="alert">
          <p>Could not check your vote status.</p>
          <button
            type="button"
            className="secondary-button"
            onClick={vote.retryStatus}
          >
            Check vote status
          </button>
        </div>
      )}

      {vote.status.kind === "not_voted" && (
        <fieldset className="reader-consultation__choice-group">
          <legend className="reader-consultation__legend">
            Choose a photo
          </legend>
          <ul className="reader-consultation__photos">
            {phase.detail.photos.map((photo, index) => (
              <li
                key={photo.id}
                className={`reader-consultation__photo${
                  selectedPhotoId === photo.id
                    ? " reader-consultation__photo--selected"
                    : ""
                }`}
              >
                <p className="reader-consultation__photo-position">
                  Photo {index + 1} of {phase.detail.photos.length}
                </p>
                <label className="reader-consultation__select-photo">
                  <img
                    src={phase.photoUrls[index]}
                    alt={`Consultation photo ${index + 1}`}
                  />
                  <span className="reader-consultation__choice">
                    <input
                      type="radio"
                      name="vote-choice"
                      value={photo.id}
                      aria-label={`Photo ${index + 1}`}
                      checked={selectedPhotoId === photo.id}
                      onChange={() => setSelectedPhotoId(photo.id)}
                    />
                    <span>
                      {selectedPhotoId === photo.id
                        ? `Photo ${index + 1} selected`
                        : `Choose photo ${index + 1}`}
                    </span>
                  </span>
                </label>
                <button
                  type="button"
                  className="reader-consultation__enlarge"
                  aria-label={`Enlarge photo ${index + 1}`}
                  onClick={() =>
                    setEnlarged({
                      src: phase.photoUrls[index],
                      alt: `Consultation photo ${index + 1}`,
                    })
                  }
                >
                  <span aria-hidden="true">↗</span>
                </button>
              </li>
            ))}
          </ul>

          {!reviewing ? (
            <div className="reader-consultation__vote-actions">
              <button
                type="button"
                className="primary-button"
                disabled={selectedPhotoId === null}
                onClick={() => setReviewing(true)}
              >
                Review vote
              </button>
            </div>
          ) : (
            <div
              className="reader-consultation__review"
              role="region"
              aria-label="Review your vote"
            >
              <h2 className="reader-consultation__review-title">
                Review your vote
              </h2>
              <p>Photo {selectedIndex + 1} will be recorded as your choice.</p>
              {selectedIndex >= 0 && (
                <img
                  className="reader-consultation__review-image"
                  src={phase.photoUrls[selectedIndex]}
                  alt={`Selected photo ${selectedIndex + 1}`}
                />
              )}
              <p className="reader-consultation__finality">
                Votes are final and cannot be changed.
              </p>

              {vote.outcome === "invalid_selection" && (
                <p className="field-error" role="alert">
                  That photo is not part of this consultation.
                </p>
              )}
              {vote.outcome === "retryable" && (
                <p className="field-error" role="alert">
                  Your vote was not recorded. Please try again.
                </p>
              )}
              {vote.outcome === "unknown" && (
                <div className="reader-consultation__unknown">
                  <p className="field-error" role="alert">
                    We couldn&apos;t confirm whether your vote was recorded.
                  </p>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void vote.checkStatus()}
                  >
                    Check vote status
                  </button>
                </div>
              )}

              <div className="reader-consultation__review-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setReviewing(false)}
                >
                  Back to photos
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setReviewing(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="primary-button"
                  disabled={vote.submitting || selectedPhotoId === null}
                  onClick={() => {
                    if (selectedPhotoId !== null) {
                      void vote.submit(selectedPhotoId);
                    }
                  }}
                >
                  {vote.submitting ? "Confirming…" : "Confirm vote"}
                </button>
              </div>
            </div>
          )}
        </fieldset>
      )}

      {vote.status.kind === "voted" && (
        <>
          <ul className="reader-consultation__photos">
            {phase.detail.photos.map((photo, index) => {
              const isVoted = votedPhotoId === photo.id;
              return (
                <li
                  key={photo.id}
                  className={`reader-consultation__photo${
                    isVoted ? " reader-consultation__photo--voted" : ""
                  }`}
                >
                  <span className="reader-consultation__photo-position">
                    Photo {index + 1} of {phase.detail.photos.length}
                  </span>
                  <button
                    type="button"
                    className="reader-consultation__view-photo"
                    aria-label={`Enlarge photo ${index + 1}`}
                    onClick={() =>
                      setEnlarged({
                        src: phase.photoUrls[index],
                        alt: `Consultation photo ${index + 1}`,
                      })
                    }
                  >
                    <img
                      src={phase.photoUrls[index]}
                      alt={`Consultation photo ${index + 1}`}
                    />
                  </button>
                  {isVoted && (
                    <span className="reader-consultation__your-vote">
                      Your vote
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
          <p className="reader-consultation__finality" role="status">
            Votes cannot be changed.
          </p>
        </>
      )}

      <div className="reader-consultation__actions">
        <button
          type="button"
          className="secondary-button"
          onClick={retryProtectedState}
        >
          Refresh
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          {exitLabel}
        </button>
      </div>

      {enlarged !== null && (
        <PhotoEnlargement
          src={enlarged.src}
          alt={enlarged.alt}
          onClose={() => setEnlarged(null)}
        />
      )}
    </section>
  );
}

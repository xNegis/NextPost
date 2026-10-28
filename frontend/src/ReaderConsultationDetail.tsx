import { useState } from "react";

import { ConsultationTextDisplay } from "./ConsultationTextDisplay";
import { formatPublishedDate } from "./consultationDate";
import { PhotoCarousel } from "./PhotoCarousel";
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
  const [enlargedIndex, setEnlargedIndex] = useState<number | null>(null);
  const [activePhotoIndex, setActivePhotoIndex] = useState(0);
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
  const activePhoto =
    phase.detail.photos[activePhotoIndex] ?? phase.detail.photos[0];
  const activePhotoNumber = activePhotoIndex + 1;

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
          <PhotoCarousel
            label="Consultation photos"
            items={phase.detail.photos.map((photo, index) => ({
              id: photo.id,
              src: phase.photoUrls[index],
              alt: `Consultation photo ${index + 1}`,
              width: photo.width,
              height: photo.height,
              badge:
                selectedPhotoId === photo.id ? (
                  <span className="photo-carousel__vote-badge">Selected</span>
                ) : undefined,
            }))}
            onActiveIndexChange={setActivePhotoIndex}
            onEnlarge={(_item, index) => setEnlargedIndex(index)}
          />

          {!reviewing ? (
            <div className="reader-consultation__vote-panel">
              <div className="reader-consultation__vote-panel-copy">
                <span>Viewing photo {activePhotoNumber}</span>
                {selectedIndex >= 0 && (
                  <strong>Photo {selectedIndex + 1} selected</strong>
                )}
              </div>
              <button
                type="button"
                className="secondary-button reader-consultation__choose-visible"
                aria-pressed={activePhoto?.id === selectedPhotoId}
                disabled={activePhoto === undefined}
                onClick={() => {
                  if (activePhoto !== undefined)
                    setSelectedPhotoId(activePhoto.id);
                }}
              >
                {activePhoto?.id === selectedPhotoId
                  ? "Selected"
                  : "Choose this photo"}
              </button>
              {selectedPhotoId !== null && (
                <button
                  type="button"
                  className="primary-button reader-consultation__review-visible"
                  onClick={() => setReviewing(true)}
                >
                  Review vote
                </button>
              )}
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
          <PhotoCarousel
            label="Consultation photos"
            items={phase.detail.photos.map((photo, index) => ({
              id: photo.id,
              src: phase.photoUrls[index],
              alt: `Consultation photo ${index + 1}`,
              width: photo.width,
              height: photo.height,
              badge:
                votedPhotoId === photo.id ? (
                  <span className="photo-carousel__vote-badge">Your vote</span>
                ) : undefined,
            }))}
            onEnlarge={(_item, index) => setEnlargedIndex(index)}
          />
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

      {enlargedIndex !== null && (
        <PhotoEnlargement
          items={phase.detail.photos.map((photo, index) => ({
            id: photo.id,
            src: phase.photoUrls[index],
            alt: `Consultation photo ${index + 1}`,
            width: photo.width,
            height: photo.height,
            badge:
              vote.status.kind === "voted" &&
              vote.status.photoId === photo.id ? (
                <span className="photo-carousel__vote-badge">Your vote</span>
              ) : undefined,
          }))}
          initialIndex={enlargedIndex}
          renderAction={
            vote.status.kind === "not_voted"
              ? (index) => {
                  const photo = phase.detail.photos[index];
                  if (photo === undefined) return null;
                  return (
                    <button
                      type="button"
                      className="reader-consultation__fullscreen-choice"
                      aria-pressed={selectedPhotoId === photo.id}
                      onClick={() => setSelectedPhotoId(photo.id)}
                    >
                      {selectedPhotoId === photo.id
                        ? `Photo ${index + 1} selected`
                        : "Choose this photo"}
                    </button>
                  );
                }
              : undefined
          }
          onClose={() => setEnlargedIndex(null)}
        />
      )}
    </section>
  );
}

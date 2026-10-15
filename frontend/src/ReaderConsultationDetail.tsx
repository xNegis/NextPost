import { useState } from "react";

import { ConsultationTextDisplay } from "./ConsultationTextDisplay";
import { formatPublishedDate } from "./consultationDate";
import { PhotoEnlargement } from "./PhotoEnlargement";
import { useReaderConsultationDetail } from "./useReaderConsultationDetail";

interface ReaderConsultationDetailProps {
  consultationId: string;
  onBack: () => void;
  onSessionLost: () => void;
}

interface EnlargedPhoto {
  src: string;
  alt: string;
}

export function ReaderConsultationDetail({
  consultationId,
  onBack,
  onSessionLost,
}: ReaderConsultationDetailProps) {
  const { phase, retry } = useReaderConsultationDetail(
    consultationId,
    onSessionLost,
  );
  const [enlarged, setEnlarged] = useState<EnlargedPhoto | null>(null);

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
          Back to Home
        </button>
      </section>
    );
  }

  if (phase.kind === "unavailable") {
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
        <button type="button" className="primary-button" onClick={retry}>
          Refresh
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          Back to Home
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
          Back to Home
        </button>
      </section>
    );
  }

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
        Public · Open · Published{" "}
        <time dateTime={phase.detail.published_at}>
          {formatPublishedDate(phase.detail.published_at)}
        </time>
      </p>

      <ConsultationTextDisplay
        question={phase.detail.question}
        context={phase.detail.context}
        headingLevel={2}
      />

      {phase.photoUrls.length > 0 && (
        <ul className="reader-consultation__photos">
          {phase.photoUrls.map((url, index) => (
            <li key={url} className="reader-consultation__photo">
              <button
                type="button"
                className="reader-consultation__enlarge"
                aria-label={`Enlarge photo ${index + 1}`}
                onClick={() =>
                  setEnlarged({
                    src: url,
                    alt: `Consultation photo ${index + 1}`,
                  })
                }
              >
                <img src={url} alt={`Consultation photo ${index + 1}`} />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="reader-consultation__actions">
        <button type="button" className="secondary-button" onClick={retry}>
          Refresh
        </button>
        <button type="button" className="secondary-button" onClick={onBack}>
          Back to Home
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

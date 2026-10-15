import { ConsultationTextDisplay } from "./ConsultationTextDisplay";
import { PRIVATE } from "./audience";
import type { Audience } from "./audience";

interface PublishSummaryProps {
  question: string;
  context: string | null;
  audience: Audience;
  photoCount: number;
  pending: boolean;
  error: string | null;
  onPublish: () => void;
  onBackToEdit: () => void;
}

export function PublishSummary({
  question,
  context,
  audience,
  photoCount,
  pending,
  error,
  onPublish,
  onBackToEdit,
}: PublishSummaryProps) {
  const reach =
    audience === PRIVATE
      ? "Only people with the link and an account can see this consultation."
      : "Anyone with an account can find and see this consultation.";

  return (
    <div className="publish-summary">
      <ConsultationTextDisplay
        question={question}
        context={context}
        headingLevel={3}
      />

      <p className="publish-summary__photos">
        {photoCount} {photoCount === 1 ? "photo" : "photos"} will be published.
      </p>

      <p className="publish-summary__reach">{reach}</p>

      <p className="publish-summary__note">
        Published content can&apos;t be edited, and this consultation
        doesn&apos;t expire.
      </p>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <div className="publish-summary__actions">
        <button
          type="button"
          className="primary-button"
          disabled={pending}
          onClick={onPublish}
        >
          {pending
            ? "Publishing…"
            : error
              ? "Try again"
              : "Publish consultation"}
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={pending}
          onClick={onBackToEdit}
        >
          Back to edit
        </button>
      </div>
    </div>
  );
}

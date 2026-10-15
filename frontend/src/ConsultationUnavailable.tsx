interface ConsultationUnavailableProps {
  kind: "unavailable" | "error";
  onBack: () => void;
  onRetry?: () => void;
}

export function ConsultationUnavailable({
  kind,
  onBack,
  onRetry,
}: ConsultationUnavailableProps) {
  if (kind === "error") {
    return (
      <div className="consultation-unavailable" role="alert">
        <h2>Something went wrong.</h2>
        <p>
          We couldn&apos;t load this consultation. Check your connection and try
          again.
        </p>
        <div className="consultation-unavailable__actions">
          {onRetry && (
            <button type="button" className="primary-button" onClick={onRetry}>
              Retry
            </button>
          )}
          <button type="button" className="secondary-button" onClick={onBack}>
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="consultation-unavailable">
      <h2>This consultation is unavailable.</h2>
      <p>It may have ended or been removed.</p>
      <div className="consultation-unavailable__actions">
        <button type="button" className="secondary-button" onClick={onBack}>
          Back to Home
        </button>
      </div>
    </div>
  );
}

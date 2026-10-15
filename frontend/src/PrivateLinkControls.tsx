import { useCallback, useEffect, useRef, useState } from "react";

export type PrivateLinkStatus = "active" | "disabled";

interface PrivateLinkControlsProps {
  status: PrivateLinkStatus;
  link: string | null;
  pending: boolean;
  error?: string;
  onCopy: (link: string) => void;
  onDisable: () => void;
  onReplace: () => void;
  onCreateNew: () => void;
  onRefresh?: () => void;
}

type Confirmation = "disable" | "replace" | null;

export function PrivateLinkControls({
  status,
  link,
  pending,
  error,
  onCopy,
  onDisable,
  onReplace,
  onCreateNew,
  onRefresh,
}: PrivateLinkControlsProps) {
  const [confirmation, setConfirmation] = useState<Confirmation>(null);
  const confirmationActionRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (confirmation !== null) confirmationActionRef.current?.focus();
  }, [confirmation]);

  const handleCopy = useCallback(() => {
    if (link !== null) onCopy(link);
  }, [link, onCopy]);

  if (status === "disabled") {
    return (
      <div className="private-link-controls">
        <h3>Private link</h3>
        <p className="private-link-controls__status">Link disabled</p>
        <button
          type="button"
          className="secondary-button"
          disabled={pending}
          onClick={onCreateNew}
        >
          Create new link
        </button>
        {error && (
          <div className="private-link-controls__error" role="alert">
            <p>{error}</p>
            {onRefresh && (
              <button
                type="button"
                className="secondary-button"
                disabled={pending}
                onClick={onRefresh}
              >
                Refresh link
              </button>
            )}
          </div>
        )}
      </div>
    );
  }

  if (confirmation === "disable") {
    return (
      <div className="private-link-controls">
        <h3>Disable link?</h3>
        <p>People with the current link will no longer be able to see it.</p>
        <div className="private-link-controls__actions">
          <button
            ref={confirmationActionRef}
            type="button"
            className="primary-button"
            disabled={pending}
            onClick={() => {
              setConfirmation(null);
              onDisable();
            }}
          >
            Disable link
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={pending}
            onClick={() => setConfirmation(null)}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (confirmation === "replace") {
    return (
      <div className="private-link-controls">
        <h3>Replace link?</h3>
        <p>
          The current link will stop working and a new link will be created.
        </p>
        <div className="private-link-controls__actions">
          <button
            ref={confirmationActionRef}
            type="button"
            className="primary-button"
            disabled={pending}
            onClick={() => {
              setConfirmation(null);
              onReplace();
            }}
          >
            Replace link
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={pending}
            onClick={() => setConfirmation(null)}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="private-link-controls">
      <h3>Private link</h3>
      <p className="private-link-controls__status">Current link</p>
      {link !== null && <p className="private-link-controls__link">{link}</p>}
      <div className="private-link-controls__actions">
        <button
          type="button"
          className="secondary-button"
          disabled={pending || link === null}
          onClick={handleCopy}
        >
          Copy link
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={pending}
          onClick={() => setConfirmation("disable")}
        >
          Disable link
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={pending}
          onClick={() => setConfirmation("replace")}
        >
          Replace link
        </button>
      </div>
      {error && (
        <div className="private-link-controls__error" role="alert">
          <p>{error}</p>
          {onRefresh && (
            <button
              type="button"
              className="secondary-button"
              disabled={pending}
              onClick={onRefresh}
            >
              Refresh link
            </button>
          )}
        </div>
      )}
    </div>
  );
}

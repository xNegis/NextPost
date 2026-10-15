import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import { usePhotoUploader } from "./usePhotoUploader";
import type { PhotoItem } from "./usePhotoUploader";
import type { ApplicationConfig } from "./photoApi";

const ACCEPT_TYPES = "image/jpeg,image/png,image/webp,image/heic,image/heif";

export interface PhotoUploaderSnapshot {
  items: PhotoItem[];
  config: ApplicationConfig | null;
  readyImageIds: string[];
  isPublishBlocked: boolean;
  sessionInactive: boolean;
  sessionId: string | null;
}

export interface PhotoUploaderHandle {
  discard: () => void;
  relinquish: () => void;
  setFrozen: (frozen: boolean) => void;
}

interface PhotoUploaderProps {
  onSnapshot?: (snapshot: PhotoUploaderSnapshot) => void;
  onSessionLost?: () => void;
}

export const PhotoUploader = forwardRef<
  PhotoUploaderHandle,
  PhotoUploaderProps
>(function PhotoUploader({ onSnapshot, onSessionLost }, ref) {
  const inputRef = useRef<HTMLInputElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const [enlarged, setEnlarged] = useState<PhotoItem | null>(null);

  const {
    items,
    config,
    readyImageIds,
    isPublishBlocked,
    sessionInactive,
    cleanupError,
    sessionId,
    addFiles,
    removeItem,
    retryItem,
    discard,
    relinquish,
    setFrozen,
  } = usePhotoUploader(onSessionLost ?? (() => undefined));

  useImperativeHandle(ref, () => ({ discard, relinquish, setFrozen }), [
    discard,
    relinquish,
    setFrozen,
  ]);

  const snapshotRef = useRef(onSnapshot);
  snapshotRef.current = onSnapshot;

  useEffect(() => {
    snapshotRef.current?.({
      items,
      config,
      readyImageIds,
      isPublishBlocked,
      sessionInactive,
      sessionId,
    });
  }, [
    items,
    config,
    readyImageIds,
    isPublishBlocked,
    sessionInactive,
    sessionId,
  ]);

  const openEnlarged = useCallback((item: PhotoItem) => {
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    setEnlarged(item);
  }, []);

  const closeEnlarged = useCallback(() => {
    setEnlarged(null);
    const target = returnFocusRef.current;
    if (target && target.isConnected) {
      target.focus();
    }
    returnFocusRef.current = null;
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Escape") {
        closeEnlarged();
      } else if (event.key === "Tab") {
        event.preventDefault();
        closeButtonRef.current?.focus();
      }
    },
    [closeEnlarged],
  );

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    addFiles(Array.from(files));
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  return (
    <div className="photo-uploader">
      <div className="photo-uploader__header">
        <p className="photo-uploader__guidance">
          {config
            ? `Add between ${config.consultation_min_photos} and ${config.consultation_max_photos} photos for people to compare.`
            : "Loading photo limits…"}
        </p>
        <button
          type="button"
          className="primary-button"
          disabled={!config}
          onClick={() => inputRef.current?.click()}
        >
          Add photos
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT_TYPES}
          multiple
          disabled={!config}
          className="photo-uploader__input"
          aria-label="Choose photos"
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      {cleanupError && (
        <p className="form-error" role="alert">
          {cleanupError}
        </p>
      )}

      {sessionInactive && (
        <p className="form-error" role="alert">
          Your upload session expired. Please select your photos again.
        </p>
      )}

      {items.length > 0 && (
        <ul className="photo-list">
          {items.map((item, index) => (
            <li key={item.clientId} className="photo-item">
              {item.status === "ready" && item.imageUrl ? (
                <img
                  src={item.imageUrl}
                  alt={`Selected photo ${index + 1}`}
                  className="photo-item__image"
                />
              ) : (
                <div className="photo-item__placeholder" aria-hidden="true" />
              )}

              <div className="photo-item__meta">
                {item.status === "uploading" && (
                  <>
                    <span className="photo-item__status">Uploading…</span>
                    <progress
                      className="photo-item__progress"
                      value={Math.round(item.progress * 100)}
                      max={100}
                      aria-label={`Upload progress ${index + 1}`}
                    />
                  </>
                )}
                {item.status === "processing" && (
                  <span className="photo-item__status" role="status">
                    Processing photo…
                  </span>
                )}
                {item.status === "ready" && (
                  <span className="photo-item__status" role="status">
                    Ready
                  </span>
                )}
                {item.status === "error" && (
                  <span
                    className="photo-item__status photo-item__status--error"
                    role="alert"
                  >
                    {item.error}
                  </span>
                )}
              </div>

              <div className="photo-item__actions">
                {item.status === "error" && (
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => retryItem(item.clientId)}
                  >
                    Try again
                  </button>
                )}
                {item.status === "ready" && (
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => openEnlarged(item)}
                  >
                    Enlarge
                  </button>
                )}
                <button
                  type="button"
                  className="secondary-button photo-item__remove"
                  onClick={() => removeItem(item.clientId)}
                >
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {enlarged && enlarged.imageUrl && (
        <div
          className="photo-modal"
          role="dialog"
          aria-modal="true"
          aria-label="Photo preview"
          onKeyDown={handleKeyDown}
        >
          <div className="photo-modal__backdrop" onClick={closeEnlarged} />
          <div className="photo-modal__panel">
            <img
              src={enlarged.imageUrl}
              alt={`Selected photo ${items.indexOf(enlarged) + 1}`}
              className="photo-modal__image"
            />
            <button
              ref={closeButtonRef}
              type="button"
              className="primary-button photo-modal__close"
              autoFocus
              onClick={closeEnlarged}
            >
              Close preview
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

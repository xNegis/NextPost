import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { ApiError } from "./api";
import {
  finalizeConsultation,
  type ConsultationPhoto,
  type FinalizeDeclaration,
} from "./consultationApi";

const FOCUSABLE_SELECTOR =
  "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), " +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface FinalizeConsultationDialogProps {
  consultationId: string;
  photos: ConsultationPhoto[];
  onCancel: () => void;
  onFinalized: () => void;
  onReload: () => void;
  onSessionLost: () => void;
}

function newOperationId(): string {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi && typeof cryptoApi.randomUUID === "function") {
    return cryptoApi.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = Math.floor(Math.random() * 16);
    const value = char === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

function selectionLabel(
  selectedIds: string[],
  chooseNone: boolean,
  photos: ConsultationPhoto[],
): string {
  if (chooseNone) return "No choice";
  const numbers = photos
    .map((photo, index) => ({ id: photo.id, number: index + 1 }))
    .filter(({ id }) => selectedIds.includes(id))
    .map(({ number }) => `Photo ${number}`);
  return numbers.join(", ");
}

export function FinalizeConsultationDialog({
  consultationId,
  photos,
  onCancel,
  onFinalized,
  onReload,
  onSessionLost,
}: FinalizeConsultationDialogProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [chooseNone, setChooseNone] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const backRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<Element | null>(null);
  const operationIdRef = useRef<string>(newOperationId());
  const callbacksRef = useRef({
    onCancel,
    onFinalized,
    onReload,
    onSessionLost,
  });

  useEffect(() => {
    callbacksRef.current = { onCancel, onFinalized, onReload, onSessionLost };
  });

  useEffect(() => {
    previousFocusRef.current = document.activeElement;
    cancelRef.current?.focus();
    const root = document.getElementById("root");
    root?.setAttribute("inert", "");
    return () => {
      root?.removeAttribute("inert");
      const previous = previousFocusRef.current;
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, []);

  useEffect(() => {
    if (reviewing) backRef.current?.focus();
  }, [reviewing]);

  useEffect(() => {
    const handler = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        if (!pending) callbacksRef.current.onCancel();
        return;
      }
      if (event.key !== "Tab") return;
      const panel = panelRef.current;
      if (panel === null) return;
      const focusable = Array.from(
        panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      ).filter((element) => element.tabIndex >= 0);
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      if (event.shiftKey) {
        if (active === first || !panel.contains(active)) {
          event.preventDefault();
          last.focus();
        }
      } else if (active === last || !panel.contains(active)) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [pending]);

  function togglePhoto(id: string) {
    setChooseNone(false);
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((existing) => existing !== id)
        : [...current, id],
    );
  }

  function toggleNone() {
    setChooseNone((current) => !current);
    setSelectedIds([]);
  }

  function handleReview() {
    if (!valid) return;
    setError(null);
    setReviewing(true);
  }

  function handleBack() {
    setError(null);
    setReviewing(false);
  }

  const valid = chooseNone || selectedIds.length > 0;

  async function handleConfirm() {
    if (pending || !valid) return;
    setPending(true);
    setError(null);

    const orderedSelection = photos
      .filter((photo) => selectedIds.includes(photo.id))
      .map((photo) => photo.id);
    const declaration: FinalizeDeclaration = chooseNone
      ? { kind: "none", option_ids: [] }
      : { kind: "selected", option_ids: orderedSelection };

    try {
      await finalizeConsultation(
        consultationId,
        operationIdRef.current,
        declaration,
      );
      callbacksRef.current.onFinalized();
    } catch (reason) {
      if (reason instanceof ApiError) {
        if (reason.code === "unauthenticated") {
          callbacksRef.current.onSessionLost();
          return;
        }
        if (
          reason.code === "consultation_conflict" ||
          reason.code === "consultation_unavailable"
        ) {
          callbacksRef.current.onReload();
          return;
        }
      }
      setError("Could not finalize the consultation. Try again.");
      setPending(false);
    }
  }

  return createPortal(
    <div
      className="finalize-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="finalize-dialog-title"
      aria-describedby="finalize-dialog-description"
    >
      <div
        className="finalize-dialog__backdrop"
        onClick={() => {
          if (!pending) onCancel();
        }}
      />
      <div className="finalize-dialog__panel" ref={panelRef}>
        <h2 id="finalize-dialog-title">Finalize consultation?</h2>
        <p id="finalize-dialog-description">
          Finalizing is permanent. It immediately stops new votes and access,
          removes every photograph for everyone including you, and cannot be
          undone. Vote counts may still change until you confirm.
        </p>

        {!reviewing ? (
          <>
            <fieldset className="finalize-dialog__options">
              <legend>Select the photos you chose</legend>
              <label className="finalize-dialog__none">
                <input
                  type="checkbox"
                  checked={chooseNone}
                  onChange={toggleNone}
                />
                Choose none
              </label>
              {photos.map((photo, index) => (
                <label key={photo.id} className="finalize-dialog__photo">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(photo.id)}
                    onChange={() => togglePhoto(photo.id)}
                  />
                  Photo {index + 1}
                </label>
              ))}
            </fieldset>

            <p className="finalize-dialog__summary" aria-live="polite">
              {valid
                ? `Your choice: ${selectionLabel(
                    selectedIds,
                    chooseNone,
                    photos,
                  )}`
                : "Select one or more photos, or choose none."}
            </p>

            <div className="finalize-dialog__actions">
              <button
                ref={cancelRef}
                type="button"
                className="secondary-button"
                onClick={onCancel}
                disabled={pending}
              >
                Cancel
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={handleReview}
                disabled={!valid}
              >
                Review finalization
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="finalize-dialog__review" aria-live="polite">
              Your choice: {selectionLabel(selectedIds, chooseNone, photos)}
            </p>
            <p className="finalize-dialog__review-note">
              This is your final decision. New votes and access stop immediately
              and every photograph is permanently removed.
            </p>

            {error !== null && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}

            <div className="finalize-dialog__actions">
              <button
                ref={backRef}
                type="button"
                className="secondary-button"
                onClick={handleBack}
                disabled={pending}
              >
                Back
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={onCancel}
                disabled={pending}
              >
                Cancel
              </button>
              <button
                type="button"
                className="danger-button"
                onClick={handleConfirm}
                disabled={pending}
              >
                {pending ? "Finalizing…" : "Finalize consultation"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>,
    document.body,
  );
}

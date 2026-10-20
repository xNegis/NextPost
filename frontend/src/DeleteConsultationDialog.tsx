import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { ApiError } from "./api";
import {
  deleteConsultation,
  type MyConsultationState,
} from "./consultationApi";

const FOCUSABLE_SELECTOR =
  "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), " +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface DeleteConsultationDialogProps {
  consultationId: string;
  state: MyConsultationState;
  onCancel: () => void;
  onDeleted: () => void;
  onReload: () => void;
  onSessionLost: () => void;
}

const OPEN_DESCRIPTION =
  "Access ends immediately. Every photograph is permanently scheduled for " +
  "deletion and all votes are discarded without creating a result. This " +
  "cannot be undone.";

const FINALIZED_DESCRIPTION =
  "This consultation will disappear from My consultations. Photographs remain " +
  "unavailable and only minimum private photo-free participant outcomes may " +
  "remain. This cannot be undone.";

export function DeleteConsultationDialog({
  consultationId,
  state,
  onCancel,
  onDeleted,
  onReload,
  onSessionLost,
}: DeleteConsultationDialogProps) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<Element | null>(null);
  const callbacksRef = useRef({ onCancel, onDeleted, onReload, onSessionLost });

  useEffect(() => {
    callbacksRef.current = { onCancel, onDeleted, onReload, onSessionLost };
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

  async function handleConfirm() {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await deleteConsultation(consultationId, state);
      callbacksRef.current.onDeleted();
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
      setError("Could not delete the consultation. Try again.");
      setPending(false);
    }
  }

  const description =
    state === "open" ? OPEN_DESCRIPTION : FINALIZED_DESCRIPTION;

  return createPortal(
    <div
      className="delete-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
      aria-describedby="delete-dialog-description"
    >
      <div
        className="delete-dialog__backdrop"
        onClick={() => {
          if (!pending) onCancel();
        }}
      />
      <div className="delete-dialog__panel" ref={panelRef}>
        <h2 id="delete-dialog-title">Delete consultation?</h2>
        <p id="delete-dialog-description">{description}</p>
        {error !== null && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="delete-dialog__actions">
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
            className="danger-button"
            onClick={handleConfirm}
            disabled={pending}
          >
            {pending ? "Deleting…" : "Delete consultation"}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

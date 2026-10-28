import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

import { PhotoCarousel, type PhotoCarouselItem } from "./PhotoCarousel";

const FOCUSABLE_SELECTOR =
  "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), " +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface PhotoEnlargementProps {
  items: PhotoCarouselItem[];
  initialIndex: number;
  onClose: () => void;
}

export function PhotoEnlargement({
  items,
  initialIndex,
  onClose,
}: PhotoEnlargementProps) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<Element | null>(null);

  useEffect(() => {
    previousFocusRef.current = document.activeElement;
    closeRef.current?.focus();

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
        onClose();
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
  }, [onClose]);

  return createPortal(
    <div
      className="photo-enlargement"
      role="dialog"
      aria-modal="true"
      aria-label="Full-screen photo gallery"
    >
      <div className="photo-enlargement__backdrop" onClick={onClose} />
      <div className="photo-enlargement__panel" ref={panelRef}>
        <PhotoCarousel
          items={items}
          label="Full-screen consultation photos"
          initialIndex={initialIndex}
        />
        <button
          ref={closeRef}
          type="button"
          className="secondary-button photo-enlargement__close"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>,
    document.body,
  );
}

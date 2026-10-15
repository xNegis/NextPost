import { useEffect, useRef } from "react";

interface PhotoEnlargementProps {
  src: string;
  alt: string;
  onClose: () => void;
}

export function PhotoEnlargement({ src, alt, onClose }: PhotoEnlargementProps) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<Element | null>(null);

  useEffect(() => {
    previousFocusRef.current = document.activeElement;
    closeRef.current?.focus();
    return () => {
      const previous = previousFocusRef.current;
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, []);

  useEffect(() => {
    const handler = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="photo-enlargement"
      role="dialog"
      aria-modal="true"
      aria-label={alt}
    >
      <div className="photo-enlargement__backdrop" onClick={onClose} />
      <div className="photo-enlargement__panel">
        <img className="photo-enlargement__image" src={src} alt={alt} />
        <button
          ref={closeRef}
          type="button"
          className="secondary-button photo-enlargement__close"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  );
}

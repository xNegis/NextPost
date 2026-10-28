import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
  type UIEvent,
} from "react";

export interface PhotoCarouselItem {
  id: string;
  src: string;
  alt: string;
  footer?: ReactNode;
  badge?: ReactNode;
}

interface PhotoCarouselProps {
  items: PhotoCarouselItem[];
  label: string;
  onEnlarge?: (item: PhotoCarouselItem, index: number) => void;
}

export function PhotoCarousel({ items, label, onEnlarge }: PhotoCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const trackRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    setActiveIndex((current) =>
      Math.min(current, Math.max(items.length - 1, 0)),
    );
  }, [items.length]);

  if (items.length === 0) return null;

  function goTo(index: number) {
    const next = Math.max(0, Math.min(index, items.length - 1));
    setActiveIndex(next);
    const track = trackRef.current;
    if (track !== null && typeof track.scrollTo === "function") {
      track.scrollTo({ left: track.clientWidth * next, behavior: "smooth" });
    }
  }

  function handleScroll(event: UIEvent<HTMLUListElement>) {
    const track = event.currentTarget;
    if (track.clientWidth <= 0) return;
    const next = Math.max(
      0,
      Math.min(
        Math.round(track.scrollLeft / track.clientWidth),
        items.length - 1,
      ),
    );
    setActiveIndex(next);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLUListElement>) {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      goTo(activeIndex - 1);
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      goTo(activeIndex + 1);
    }
  }

  return (
    <section className="photo-carousel" aria-label={label}>
      <span className="photo-carousel__position" aria-live="polite">
        Photo {activeIndex + 1} of {items.length}
      </span>

      <ul
        ref={trackRef}
        className="photo-carousel__track"
        aria-label={`${label}. Swipe horizontally to browse.`}
        tabIndex={0}
        onScroll={handleScroll}
        onKeyDown={handleKeyDown}
      >
        {items.map((item, index) => (
          <li
            key={item.id}
            className="photo-carousel__slide"
            aria-hidden={index === activeIndex ? undefined : true}
          >
            <div className="photo-carousel__image-frame">
              <img src={item.src} alt={item.alt} />
              {item.badge}
              {onEnlarge !== undefined && index === activeIndex && (
                <button
                  type="button"
                  className="photo-carousel__enlarge"
                  aria-label={`Enlarge photo ${index + 1}`}
                  onClick={() => onEnlarge(item, index)}
                >
                  <span aria-hidden="true">↗</span>
                </button>
              )}
            </div>
            {index === activeIndex && item.footer !== undefined && (
              <div className="photo-carousel__footer">{item.footer}</div>
            )}
          </li>
        ))}
      </ul>
      {items.length > 1 && (
        <div className="photo-carousel__dots" aria-hidden="true">
          {items.map((item, index) => (
            <span
              key={item.id}
              className={`photo-carousel__dot${
                index === activeIndex ? " photo-carousel__dot--active" : ""
              }`}
            />
          ))}
        </div>
      )}
    </section>
  );
}

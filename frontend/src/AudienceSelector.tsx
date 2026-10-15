import {
  forwardRef,
  useCallback,
  useId,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import { AUDIENCE_MISSING_MESSAGE, PRIVATE, PUBLIC } from "./audience";
import type { Audience } from "./audience";

export interface AudienceSelectorHandle {
  validateAndFocus: () => Audience | null;
}

interface AudienceSelectorProps {
  value: Audience | null;
  onChange: (value: Audience | null) => void;
  serverError?: string;
  onServerErrorClear: () => void;
}

export const AudienceSelector = forwardRef<
  AudienceSelectorHandle,
  AudienceSelectorProps
>(function AudienceSelector(
  { value, onChange, serverError, onServerErrorClear },
  ref,
) {
  const [localError, setLocalError] = useState<string | null>(null);
  const publicRef = useRef<HTMLInputElement>(null);
  const id = useId();
  const groupName = `${id}-audience`;
  const publicDescriptionId = `${id}-public-description`;
  const privateDescriptionId = `${id}-private-description`;

  const handleChange = useCallback(
    (next: Audience) => {
      onChange(next);
      onServerErrorClear();
      setLocalError(null);
    },
    [onChange, onServerErrorClear],
  );

  useImperativeHandle(
    ref,
    () => ({
      validateAndFocus: () => {
        if (value === null) {
          setLocalError(AUDIENCE_MISSING_MESSAGE);
          publicRef.current?.focus();
          return null;
        }
        setLocalError(null);
        return value;
      },
    }),
    [value],
  );

  const error = localError ?? serverError ?? null;
  const noteId = `${id}-note`;
  const errorId = `${id}-error`;
  const describedBy = [error ? errorId : null, noteId]
    .filter(Boolean)
    .join(" ");

  return (
    <fieldset className="audience-selector" aria-describedby={describedBy}>
      <legend className="audience-selector__legend">Who can see it?</legend>

      <div className="audience-option">
        <label className="audience-option__label">
          <input
            ref={publicRef}
            type="radio"
            name={groupName}
            value={PUBLIC}
            checked={value === PUBLIC}
            aria-invalid={error ? true : undefined}
            aria-describedby={publicDescriptionId}
            onChange={() => handleChange(PUBLIC)}
          />
          <span className="audience-option__title">Public</span>
        </label>
        <p id={publicDescriptionId} className="audience-option__description">
          Anyone with an account can find and see it in the feed.
        </p>
      </div>

      <div className="audience-option">
        <label className="audience-option__label">
          <input
            type="radio"
            name={groupName}
            value={PRIVATE}
            checked={value === PRIVATE}
            aria-invalid={error ? true : undefined}
            aria-describedby={privateDescriptionId}
            onChange={() => handleChange(PRIVATE)}
          />
          <span className="audience-option__title">Private</span>
        </label>
        <p id={privateDescriptionId} className="audience-option__description">
          Unlisted. Only people with the link and an account can see it.
        </p>
      </div>

      <p id={noteId} className="audience-selector__note">
        Only people who are signed in can see your photos.
      </p>

      {error && (
        <p id={errorId} className="field-error" role="alert">
          {error}
        </p>
      )}
    </fieldset>
  );
});

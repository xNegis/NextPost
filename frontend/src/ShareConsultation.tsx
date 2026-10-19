import { useCallback, useEffect, useState } from "react";

const SHARE_TITLE = "NextPost";
const SHARE_TEXT = "Vote on a photo consultation in NextPost";

interface ShareConsultationProps {
  link: string | null;
}

type Feedback =
  | { kind: "idle" }
  | { kind: "copied" }
  | { kind: "copy_failed" }
  | { kind: "share_completed" }
  | { kind: "share_error" };

function canSharePayload(url: string): boolean {
  if (typeof navigator.share !== "function") return false;
  if (typeof navigator.canShare === "function") {
    try {
      return navigator.canShare({ title: SHARE_TITLE, text: SHARE_TEXT, url });
    } catch {
      return false;
    }
  }
  return true;
}

async function copyText(text: string): Promise<boolean> {
  try {
    if (typeof navigator.clipboard?.writeText === "function") {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    return false;
  }
  return false;
}

export function ShareConsultation({ link }: ShareConsultationProps) {
  const [feedback, setFeedback] = useState<Feedback>({ kind: "idle" });
  const [sharePending, setSharePending] = useState(false);

  useEffect(() => {
    setFeedback({ kind: "idle" });
    setSharePending(false);
  }, [link]);

  const handleCopy = useCallback(() => {
    if (link === null) return;
    setFeedback({ kind: "idle" });
    void copyText(link).then((ok) => {
      setFeedback(ok ? { kind: "copied" } : { kind: "copy_failed" });
    });
  }, [link]);

  const handleShare = useCallback(() => {
    if (link === null || sharePending) return;
    setSharePending(true);
    setFeedback({ kind: "idle" });
    let shareResult: Promise<void>;
    try {
      shareResult = navigator.share({
        title: SHARE_TITLE,
        text: SHARE_TEXT,
        url: link,
      });
    } catch {
      setFeedback({ kind: "share_error" });
      setSharePending(false);
      return;
    }
    void shareResult
      .then(() => {
        setFeedback({ kind: "share_completed" });
      })
      .catch((error: unknown) => {
        if (
          typeof error === "object" &&
          error !== null &&
          "name" in error &&
          error.name === "AbortError"
        ) {
          setFeedback({ kind: "idle" });
        } else {
          setFeedback({ kind: "share_error" });
        }
      })
      .finally(() => {
        setSharePending(false);
      });
  }, [link, sharePending]);

  if (link === null) {
    return (
      <p className="share-consultation__note">
        Share is unavailable right now.
      </p>
    );
  }

  const shareSupported = canSharePayload(link);

  return (
    <div className="share-consultation">
      <label
        className="share-consultation__label"
        htmlFor="share-consultation-url"
      >
        Consultation link
      </label>
      <textarea
        key={link}
        id="share-consultation-url"
        className="share-consultation__url"
        readOnly
        rows={2}
        defaultValue={link}
        aria-label="Consultation link"
        onFocus={(event) => event.currentTarget.select()}
      />
      <div className="share-consultation__actions">
        <button type="button" className="secondary-button" onClick={handleCopy}>
          Copy link
        </button>
        {shareSupported && (
          <button
            type="button"
            className="secondary-button"
            disabled={sharePending}
            onClick={handleShare}
          >
            {sharePending ? "Sharing…" : "Share"}
          </button>
        )}
      </div>
      {feedback.kind === "copied" && (
        <p className="share-consultation__feedback" role="status">
          Link copied.
        </p>
      )}
      {feedback.kind === "copy_failed" && (
        <p
          className="share-consultation__feedback share-consultation__feedback--error"
          role="alert"
        >
          Could not copy the link. Select and copy it manually.
        </p>
      )}
      {feedback.kind === "share_completed" && (
        <p className="share-consultation__feedback" role="status">
          Share completed.
        </p>
      )}
      {feedback.kind === "share_error" && (
        <p
          className="share-consultation__feedback share-consultation__feedback--error"
          role="alert"
        >
          Could not share. Try copying the link instead.
        </p>
      )}
    </div>
  );
}

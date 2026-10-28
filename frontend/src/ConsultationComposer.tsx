import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import { AudienceSelector } from "./AudienceSelector";
import type { AudienceSelectorHandle } from "./AudienceSelector";
import { PRIVATE, PUBLIC } from "./audience";
import type { Audience } from "./audience";
import { ConsultationTextDisplay } from "./ConsultationTextDisplay";
import { ConsultationTextFields } from "./ConsultationTextFields";
import type { ConsultationTextFieldsHandle } from "./ConsultationTextFields";
import { DEFAULT_QUESTION, validateConsultationText } from "./consultationText";
import type { ConsultationCapacity } from "./consultationApi";
import { fetchConsultationCapacity } from "./consultationApi";
import type { MyConsultationState } from "./consultationApi";
import type { Destination } from "./Navigation";
import { PhotoUploader } from "./PhotoUploader";
import type {
  PhotoUploaderHandle,
  PhotoUploaderSnapshot,
} from "./PhotoUploader";
import { PublishedSuccess } from "./PublishedSuccess";
import { useConsultationConfig } from "./useConsultationConfig";
import { usePublishConsultation } from "./usePublishConsultation";
import type { PublishSnapshot } from "./usePublishConsultation";

type ComposerStep = "photos" | "details" | "review";

type CapacityState =
  | { kind: "loading" }
  | { kind: "ready"; capacity: ConsultationCapacity }
  | { kind: "cannot-start"; capacity: ConsultationCapacity }
  | { kind: "error" };

interface ConsultationComposerProps {
  onNavigate: (destination: Destination) => void;
  onSessionLost: () => void;
  onDirtyChange: (dirty: boolean) => void;
  pendingNav: Destination | null;
  onCancelNavigation: () => void;
  onViewInMyConsultations: (consultationId: string) => void;
  onDeleted?: (state: MyConsultationState) => void;
  onFinalized?: (consultationId: string) => void;
}

const STEP_ORDER: ComposerStep[] = ["photos", "details", "review"];

export function ConsultationComposer({
  onNavigate,
  onSessionLost,
  onDirtyChange,
  pendingNav,
  onCancelNavigation,
  onViewInMyConsultations,
  onDeleted,
  onFinalized,
}: ConsultationComposerProps) {
  const {
    status: configStatus,
    limits,
    retry: retryConfig,
  } = useConsultationConfig(onSessionLost);

  const [capacityState, setCapacityState] = useState<CapacityState>({
    kind: "loading",
  });
  const [capacityAttempt, setCapacityAttempt] = useState(0);

  const [step, setStep] = useState<ComposerStep>("photos");
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const [context, setContext] = useState("");
  const [audience, setAudience] = useState<Audience | null>(null);
  const [dirty, setDirty] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [snapshot, setSnapshot] = useState<PhotoUploaderSnapshot | null>(null);
  const [publishedId, setPublishedId] = useState<string | null>(null);
  const [exitDialog, setExitDialog] = useState<Destination | null>(null);

  const uploaderRef = useRef<PhotoUploaderHandle>(null);
  const textFieldsRef = useRef<ConsultationTextFieldsHandle>(null);
  const audienceRef = useRef<AudienceSelectorHandle>(null);
  const exitActionRef = useRef<HTMLButtonElement>(null);
  const publishedRef = useRef(false);

  const publish = usePublishConsultation(onSessionLost);

  const markDirty = useCallback(() => {
    setDirty(true);
  }, []);

  useEffect(() => {
    let active = true;
    setCapacityState({ kind: "loading" });
    void fetchConsultationCapacity()
      .then((capacity) => {
        if (!active) return;
        setCapacityState(
          capacity.can_start
            ? { kind: "ready", capacity }
            : { kind: "cannot-start", capacity },
        );
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.code === "unauthenticated") {
          onSessionLost();
          return;
        }
        setCapacityState({ kind: "error" });
      });
    return () => {
      active = false;
    };
  }, [capacityAttempt, onSessionLost]);

  useEffect(() => {
    onDirtyChange(dirty && !publishedRef.current);
  }, [dirty, onDirtyChange]);

  useEffect(() => {
    if (snapshot && snapshot.items.length > 0) {
      markDirty();
      setSessionExpired(false);
    }
  }, [snapshot?.items.length, markDirty]);

  useEffect(() => {
    if (pendingNav === null || publishedRef.current) return;
    if (publish.status === "pending") {
      onCancelNavigation();
      return;
    }
    setExitDialog(pendingNav);
  }, [pendingNav, publish.status, onCancelNavigation]);

  useEffect(() => {
    if (exitDialog !== null) {
      exitActionRef.current?.focus();
    }
  }, [exitDialog]);

  useEffect(() => {
    if (!dirty || publishedRef.current) return;
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  useEffect(() => {
    if (publish.status !== "success" || publish.published === null) return;
    uploaderRef.current?.relinquish();
    publishedRef.current = true;
    setDirty(false);
    setPublishedId(publish.published.id);
  }, [publish.status, publish.published]);

  useEffect(() => {
    if (publish.status !== "error" || publish.error === null) return;
    if (publish.error.code === "session_inactive") {
      uploaderRef.current?.setFrozen(false);
      uploaderRef.current?.discard();
      setStep("photos");
      setSessionExpired(true);
    }
  }, [publish.status, publish.error]);

  const handleSnapshot = useCallback((next: PhotoUploaderSnapshot) => {
    setSnapshot(next);
  }, []);

  const handleQuestionChange = useCallback(
    (value: string) => {
      setQuestion(value);
      markDirty();
    },
    [markDirty],
  );

  const handleContextChange = useCallback(
    (value: string) => {
      setContext(value);
      markDirty();
    },
    [markDirty],
  );

  const handleAudienceChange = useCallback(
    (value: Audience | null) => {
      setAudience(value);
      if (value !== null) markDirty();
    },
    [markDirty],
  );

  const handleCancel = useCallback(() => {
    if (dirty && !publishedRef.current) {
      setExitDialog("home");
    } else {
      onNavigate("home");
    }
  }, [dirty, onNavigate]);

  const handleKeepEditing = useCallback(() => {
    setExitDialog(null);
    onCancelNavigation();
  }, [onCancelNavigation]);

  const handleDiscardExit = useCallback(() => {
    const destination = exitDialog ?? "home";
    uploaderRef.current?.discard();
    publishedRef.current = false;
    setDirty(false);
    setExitDialog(null);
    onNavigate(destination);
  }, [exitDialog, onNavigate]);

  const photosValid =
    configStatus === "ready" &&
    snapshot !== null &&
    snapshot.config !== null &&
    snapshot.readyImageIds.length >= snapshot.config.consultation_min_photos &&
    snapshot.readyImageIds.length <= snapshot.config.consultation_max_photos &&
    !snapshot.isPublishBlocked &&
    !snapshot.sessionInactive;

  const handlePhotosContinue = useCallback(() => {
    setStep("details");
  }, []);

  const handleDetailsContinue = useCallback(() => {
    const textResult = textFieldsRef.current?.validateAndFocus();
    const audienceResult = audienceRef.current?.validateAndFocus();
    if (textResult?.ok === true && audienceResult !== null) {
      uploaderRef.current?.setFrozen(true);
      setStep("review");
    }
  }, []);

  const handleBackToEdit = useCallback(() => {
    uploaderRef.current?.setFrozen(false);
    setStep("details");
  }, []);

  const handlePublish = useCallback(() => {
    if (snapshot === null || snapshot.sessionId === null || limits === null) {
      return;
    }
    const textResult = validateConsultationText(question, context, limits);
    if (!textResult.ok || audience === null) return;
    uploaderRef.current?.setFrozen(true);
    const payload: PublishSnapshot = {
      sessionId: snapshot.sessionId,
      orderedImageIds: snapshot.readyImageIds,
      question: textResult.value.question,
      context: textResult.value.context,
      audience,
    };
    publish.publish(payload);
  }, [snapshot, limits, question, context, audience, publish]);

  if (publishedId !== null) {
    return (
      <PublishedSuccess
        consultationId={publishedId}
        onBack={() => onNavigate("home")}
        onViewInMyConsultations={() => onViewInMyConsultations(publishedId)}
        onDeleted={onDeleted}
        onFinalized={onFinalized}
        onSessionLost={onSessionLost}
      />
    );
  }

  if (configStatus === "loading" || capacityState.kind === "loading") {
    return (
      <section className="card composer" aria-labelledby="composer-title">
        <p className="eyebrow">NextPost</p>
        <h1 id="composer-title">New consultation</h1>
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Loading…
        </div>
      </section>
    );
  }

  if (configStatus === "error" || capacityState.kind === "error") {
    return (
      <section className="card composer" aria-labelledby="composer-title">
        <p className="eyebrow">NextPost</p>
        <h1 id="composer-title">New consultation</h1>
        <div
          className="status status--unavailable"
          role="status"
          aria-live="polite"
        >
          <span className="status__dot" aria-hidden="true" />
          Could not load the consultation setup.
        </div>
        <button
          type="button"
          className="primary-button"
          onClick={() => {
            retryConfig();
            setCapacityAttempt((value) => value + 1);
          }}
        >
          Retry
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={() => onNavigate("home")}
        >
          Back Home
        </button>
      </section>
    );
  }

  if (capacityState.kind === "cannot-start") {
    return (
      <section className="card composer" aria-labelledby="composer-title">
        <p className="eyebrow">NextPost</p>
        <h1 id="composer-title">New consultation</h1>
        <p className="summary">
          You&apos;ve reached the limit of {capacityState.capacity.limit} open
          consultations. You can&apos;t start another consultation right now.
        </p>
        <button
          type="button"
          className="primary-button"
          onClick={() => onNavigate("my")}
        >
          View my consultations
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={() => onNavigate("home")}
        >
          Back Home
        </button>
      </section>
    );
  }

  const normalizedReviewText = limits
    ? validateConsultationText(question, context, limits)
    : null;

  const readyItems =
    snapshot?.items.filter(
      (item) => item.status === "ready" && item.imageUrl,
    ) ?? [];

  return (
    <section className="card composer" aria-labelledby="composer-title">
      <p className="eyebrow">NextPost</p>
      <h1 id="composer-title">New consultation</h1>

      <ol className="composer-steps">
        {STEP_ORDER.map((value, index) => {
          const label =
            value === "photos"
              ? "Photos"
              : value === "details"
                ? "Details"
                : "Review";
          const isCurrent = value === step;
          return (
            <li
              key={value}
              className="composer-step"
              aria-current={isCurrent ? "step" : undefined}
            >
              <span className="composer-step__index">{index + 1}</span>
              <span className="composer-step__label">{label}</span>
            </li>
          );
        })}
      </ol>

      <div hidden={step !== "photos"}>
        <h2 className="composer-step-heading">Photos</h2>
        <p className="composer-hint">
          Only share photos you have permission to use.
        </p>
        {sessionExpired && (
          <p className="form-error" role="alert">
            Your photo session expired. Please select your photos again.
          </p>
        )}
        <PhotoUploader
          ref={uploaderRef}
          onSnapshot={handleSnapshot}
          onSessionLost={onSessionLost}
        />
        <div className="composer-actions">
          <button
            type="button"
            className="primary-button"
            disabled={!photosValid}
            onClick={handlePhotosContinue}
          >
            Continue
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={handleCancel}
          >
            Cancel
          </button>
        </div>
      </div>

      <div hidden={step !== "details"}>
        <h2 className="composer-step-heading">Details</h2>
        {limits && (
          <ConsultationTextFields
            ref={textFieldsRef}
            question={question}
            context={context}
            limits={limits}
            onQuestionChange={handleQuestionChange}
            onContextChange={handleContextChange}
            onServerErrorClear={() => undefined}
          />
        )}
        <AudienceSelector
          ref={audienceRef}
          value={audience}
          onChange={handleAudienceChange}
          onServerErrorClear={() => undefined}
        />
        <div className="composer-actions">
          <button
            type="button"
            className="primary-button"
            onClick={handleDetailsContinue}
          >
            Continue
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => setStep("photos")}
          >
            Back
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={handleCancel}
          >
            Cancel
          </button>
        </div>
      </div>

      <div hidden={step !== "review"}>
        <h2 className="composer-step-heading">Review and publish</h2>
        {normalizedReviewText?.ok && (
          <ConsultationTextDisplay
            question={normalizedReviewText.value.question}
            context={normalizedReviewText.value.context}
            headingLevel={3}
          />
        )}
        {readyItems.length > 0 && (
          <ul className="composer-review-photos">
            {readyItems.map((item, index) => (
              <li key={item.clientId} className="composer-review-photo">
                <p className="composer-review-photo__position">
                  Photo {index + 1} of {readyItems.length}
                </p>
                <img src={item.imageUrl} alt={`Selected photo ${index + 1}`} />
              </li>
            ))}
          </ul>
        )}
        <p className="composer-review-count">
          {readyItems.length} {readyItems.length === 1 ? "photo" : "photos"}{" "}
          will be published.
        </p>
        <p className="composer-review-reach">
          {audience === PRIVATE
            ? "Only people with the link and an account can see this consultation."
            : audience === PUBLIC
              ? "Anyone with an account can find and see this consultation."
              : ""}
        </p>
        <p className="composer-review-note">
          Published content can&apos;t be edited, and this consultation
          doesn&apos;t expire.
        </p>

        {publish.status === "error" && publish.error !== null && (
          <p className="form-error" role="alert">
            {publish.error.message}
          </p>
        )}

        <div className="composer-actions">
          <button
            type="button"
            className="primary-button"
            disabled={publish.status === "pending"}
            onClick={handlePublish}
          >
            {publish.status === "pending"
              ? "Publishing…"
              : publish.status === "error"
                ? "Try again"
                : "Publish consultation"}
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={publish.status === "pending"}
            onClick={handleBackToEdit}
          >
            Back to edit
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={publish.status === "pending"}
            onClick={handleCancel}
          >
            Cancel
          </button>
        </div>
      </div>

      {exitDialog !== null && (
        <div
          className="composer-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="exit-dialog-title"
        >
          <div
            className="composer-modal__backdrop"
            onClick={handleKeepEditing}
          />
          <div className="composer-modal__panel">
            <h2 id="exit-dialog-title">Discard this consultation?</h2>
            <p>Your changes haven&apos;t been published and will be lost.</p>
            <div className="composer-modal__actions">
              <button
                ref={exitActionRef}
                type="button"
                className="primary-button"
                onClick={handleDiscardExit}
              >
                Discard
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={handleKeepEditing}
              >
                Keep editing
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

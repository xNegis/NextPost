import {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import {
  CONTEXT_PLACEHOLDER,
  normalizedCodePointLength,
  validateConsultationText,
} from "./consultationText";
import type {
  ConsultationTextErrors,
  ConsultationTextField,
  ConsultationTextLimits,
  ConsultationTextValidationResult,
} from "./consultationText";

export interface ConsultationTextFieldsHandle {
  validateAndFocus: () => ConsultationTextValidationResult;
}

interface ConsultationTextFieldsProps {
  question: string;
  context: string;
  limits: ConsultationTextLimits;
  onQuestionChange: (value: string) => void;
  onContextChange: (value: string) => void;
  serverErrors?: ConsultationTextErrors;
  onServerErrorClear: (field: ConsultationTextField) => void;
}

function validateField(
  field: ConsultationTextField,
  question: string,
  context: string,
  limits: ConsultationTextLimits,
): string | null {
  const result = validateConsultationText(question, context, limits);
  if (result.ok) return null;
  return result.errors[field] ?? null;
}

export const ConsultationTextFields = forwardRef<
  ConsultationTextFieldsHandle,
  ConsultationTextFieldsProps
>(function ConsultationTextFields(
  {
    question,
    context,
    limits,
    onQuestionChange,
    onContextChange,
    serverErrors,
    onServerErrorClear,
  },
  ref,
) {
  const [localErrors, setLocalErrors] = useState<ConsultationTextErrors>({});
  const questionRef = useRef<HTMLInputElement>(null);
  const contextRef = useRef<HTMLTextAreaElement>(null);

  const setFieldError = useCallback(
    (field: ConsultationTextField, error: string | null) => {
      setLocalErrors((previous) => {
        const next = { ...previous };
        if (error === null) {
          delete next[field];
        } else {
          next[field] = error;
        }
        return next;
      });
    },
    [],
  );

  const handleQuestionBlur = useCallback(() => {
    setFieldError(
      "question",
      validateField("question", question, context, limits),
    );
  }, [question, context, limits, setFieldError]);

  const handleContextBlur = useCallback(() => {
    setFieldError(
      "context",
      validateField("context", question, context, limits),
    );
  }, [question, context, limits, setFieldError]);

  const handleQuestionChange = useCallback(
    (value: string) => {
      onQuestionChange(value);
      onServerErrorClear("question");
      setLocalErrors((previous) => {
        if (previous.question === undefined) return previous;
        const next = { ...previous };
        const error = validateField("question", value, context, limits);
        if (error === null) {
          delete next.question;
        } else {
          next.question = error;
        }
        return next;
      });
    },
    [onQuestionChange, onServerErrorClear, context, limits],
  );

  const handleContextChange = useCallback(
    (value: string) => {
      onContextChange(value);
      onServerErrorClear("context");
      setLocalErrors((previous) => {
        if (previous.context === undefined) return previous;
        const next = { ...previous };
        const error = validateField("context", question, value, limits);
        if (error === null) {
          delete next.context;
        } else {
          next.context = error;
        }
        return next;
      });
    },
    [onContextChange, onServerErrorClear, question, limits],
  );

  useImperativeHandle(
    ref,
    () => ({
      validateAndFocus: () => {
        const result = validateConsultationText(question, context, limits);
        if (result.ok) {
          setLocalErrors({});
          return result;
        }
        setLocalErrors(result.errors);
        if (result.errors.question !== undefined) {
          questionRef.current?.focus();
        } else if (result.errors.context !== undefined) {
          contextRef.current?.focus();
        }
        return result;
      },
    }),
    [question, context, limits],
  );

  const displayedErrors: ConsultationTextErrors = {
    ...serverErrors,
    ...localErrors,
  };
  const questionError = displayedErrors.question;
  const contextError = displayedErrors.context;

  const questionCount = normalizedCodePointLength(question, false);
  const contextCount = normalizedCodePointLength(context, true);

  const questionDescribedBy = questionError
    ? "consultation-question-count consultation-question-error"
    : "consultation-question-count";
  const contextDescribedBy = contextError
    ? "consultation-context-count consultation-context-error"
    : "consultation-context-count";

  return (
    <div className="consultation-fields">
      <div className="field">
        <label htmlFor="consultation-question">Question</label>
        <input
          ref={questionRef}
          id="consultation-question"
          type="text"
          value={question}
          aria-invalid={questionError ? true : undefined}
          aria-describedby={questionDescribedBy}
          onChange={(event) => handleQuestionChange(event.target.value)}
          onBlur={handleQuestionBlur}
        />
        <div id="consultation-question-count" className="field__meta">
          <span className="field__counter">
            {questionCount} / {limits.questionMax}
          </span>
        </div>
        {questionError && (
          <p
            id="consultation-question-error"
            className="field-error"
            role="alert"
          >
            {questionError}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor="consultation-context">Context (optional)</label>
        <textarea
          ref={contextRef}
          id="consultation-context"
          value={context}
          rows={4}
          placeholder={CONTEXT_PLACEHOLDER}
          aria-invalid={contextError ? true : undefined}
          aria-describedby={contextDescribedBy}
          onChange={(event) => handleContextChange(event.target.value)}
          onBlur={handleContextBlur}
        />
        <div id="consultation-context-count" className="field__meta">
          <span className="field__counter">
            {contextCount} / {limits.contextMax}
          </span>
        </div>
        {contextError && (
          <p
            id="consultation-context-error"
            className="field-error"
            role="alert"
          >
            {contextError}
          </p>
        )}
      </div>
    </div>
  );
});

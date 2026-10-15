export const DEFAULT_QUESTION = "Which photos should I post?";

export const CONTEXT_PLACEHOLDER =
  "For example, where will you post these photos, and what would you like people to compare?";

export interface ConsultationTextLimits {
  questionMax: number;
  contextMax: number;
}

export interface NormalizedConsultationText {
  question: string;
  context: string | null;
}

export type ConsultationTextField = "question" | "context";

export type ConsultationTextErrors = Partial<
  Record<ConsultationTextField, string>
>;

export type ConsultationTextValidationResult =
  | { ok: true; value: NormalizedConsultationText }
  | { ok: false; errors: ConsultationTextErrors };

const TRIM_CHARS =
  "[\u0009-\u000d \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]";
const LEADING_TRIM_RE = new RegExp(`^${TRIM_CHARS}+`, "u");
const TRAILING_TRIM_RE = new RegExp(`${TRIM_CHARS}+$`, "u");

export function countCodePoints(value: string): number {
  return Array.from(value).length;
}

function hasUnpairedSurrogate(value: string): boolean {
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (next < 0xdc00 || next > 0xdfff) return true;
      index += 1;
    } else if (code >= 0xdc00 && code <= 0xdfff) {
      return true;
    }
  }
  return false;
}

function containsRejectedControl(value: string): boolean {
  for (const char of value) {
    const code = char.codePointAt(0) ?? 0;
    if (
      (code >= 0x00 && code <= 0x08) ||
      code === 0x0b ||
      code === 0x0c ||
      (code >= 0x0e && code <= 0x1f) ||
      (code >= 0x7f && code <= 0x9f)
    ) {
      return true;
    }
  }
  return false;
}

function trimExplicit(value: string): string {
  return value.replace(LEADING_TRIM_RE, "").replace(TRAILING_TRIM_RE, "");
}

function normalizeField(raw: string, preserveNewlines: boolean): string | null {
  if (hasUnpairedSurrogate(raw)) return null;
  let text = raw.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  text = text.normalize("NFC");
  if (preserveNewlines) {
    text = text.replace(/\t/g, " ");
    if (containsRejectedControl(text)) return null;
  } else {
    text = text.replace(/\n/g, " ").replace(/\t/g, " ");
    if (containsRejectedControl(text)) return null;
  }
  return trimExplicit(text);
}

export function normalizeQuestion(raw: string): string | null {
  return normalizeField(raw, false);
}

export function normalizeContext(raw: string): string | null {
  return normalizeField(raw, true);
}

export function normalizedCodePointLength(
  value: string,
  preserveNewlines: boolean,
): number {
  const normalized = normalizeField(value, preserveNewlines);
  return countCodePoints(normalized ?? value);
}

export function validateConsultationText(
  question: unknown,
  context: unknown,
  limits: ConsultationTextLimits,
): ConsultationTextValidationResult {
  const errors: ConsultationTextErrors = {};
  let normalizedQuestion: string | null = null;
  let normalizedContext: string | null = null;

  if (question === null || question === undefined) {
    errors.question = "Enter a question.";
  } else if (typeof question !== "string") {
    errors.question = "Enter valid text for the question.";
  } else {
    const normalized = normalizeField(question, false);
    if (normalized === null) {
      errors.question = "Enter valid text for the question.";
    } else if (countCodePoints(normalized) === 0) {
      errors.question = "Enter a question.";
    } else if (countCodePoints(normalized) > limits.questionMax) {
      errors.question = `Use ${limits.questionMax} characters or fewer for the question.`;
    } else {
      normalizedQuestion = normalized;
    }
  }

  if (context === null || context === undefined) {
    normalizedContext = null;
  } else if (typeof context !== "string") {
    errors.context = "Enter valid text for the context.";
  } else {
    const normalized = normalizeField(context, true);
    if (normalized === null) {
      errors.context = "Enter valid text for the context.";
    } else if (countCodePoints(normalized) > limits.contextMax) {
      errors.context = `Use ${limits.contextMax} characters or fewer for the context.`;
    } else {
      normalizedContext = normalized;
    }
  }

  if (errors.question !== undefined || errors.context !== undefined) {
    return { ok: false, errors };
  }
  return {
    ok: true,
    value: {
      question: normalizedQuestion as string,
      context: normalizedContext === "" ? null : normalizedContext,
    },
  };
}

export function initialConsultationText(): {
  question: string;
  context: string;
} {
  return { question: DEFAULT_QUESTION, context: "" };
}

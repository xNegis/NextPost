import { describe, expect, it } from "vitest";

import {
  DEFAULT_QUESTION,
  countCodePoints,
  initialConsultationText,
  validateConsultationText,
} from "./consultationText";
import type { ConsultationTextLimits } from "./consultationText";

const LIMITS: ConsultationTextLimits = { questionMax: 120, contextMax: 500 };

function validate(question: unknown, context: unknown) {
  return validateConsultationText(question, context, LIMITS);
}

describe("DEFAULT_QUESTION", () => {
  it("matches the accepted editable default with 27 code points", () => {
    expect(DEFAULT_QUESTION).toBe("Which photos should I post?");
    expect(countCodePoints(DEFAULT_QUESTION)).toBe(27);
  });

  it("is the question supplied by the initialization helper", () => {
    expect(initialConsultationText()).toEqual({
      question: DEFAULT_QUESTION,
      context: "",
    });
  });
});

describe("validateConsultationText", () => {
  it("accepts the default question with absent context", () => {
    const result = validate(DEFAULT_QUESTION, null);
    expect(result).toEqual({
      ok: true,
      value: { question: DEFAULT_QUESTION, context: null },
    });
  });

  it("rejects empty and whitespace questions", () => {
    for (const raw of ["", "   ", "\t", "\u00a0\u3000"]) {
      expect(validate(raw, null)).toEqual({
        ok: false,
        errors: { question: "Enter a question." },
      });
    }
  });

  it("rejects missing and non-string questions", () => {
    for (const raw of [undefined, 123, 1.5, true, ["x"], { q: "a" }]) {
      const result = validate(raw, null);
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect([
          "Enter a question.",
          "Enter valid text for the question.",
        ]).toContain(result.errors.question);
      }
    }
  });

  it("uses the exact invalid-type message for questions", () => {
    expect(validate(123, null)).toEqual({
      ok: false,
      errors: { question: "Enter valid text for the question." },
    });
  });

  it("treats null and empty context as absent", () => {
    for (const raw of [null, undefined, "", "   ", "\n\t"]) {
      const result = validate(DEFAULT_QUESTION, raw);
      expect(result.ok).toBe(true);
      if (result.ok) expect(result.value.context).toBeNull();
    }
  });

  it("uses the exact invalid-type message for context", () => {
    expect(validate(DEFAULT_QUESTION, 123)).toEqual({
      ok: false,
      errors: { context: "Enter valid text for the context." },
    });
  });

  it("enforces the question boundary without truncating", () => {
    const atLimit = "a".repeat(120);
    expect(validate(atLimit, null)).toEqual({
      ok: true,
      value: { question: atLimit, context: null },
    });
    expect(validate("a".repeat(121), null)).toEqual({
      ok: false,
      errors: { question: "Use 120 characters or fewer for the question." },
    });
  });

  it("enforces the context boundary", () => {
    const atLimit = "a".repeat(500);
    expect(validate(DEFAULT_QUESTION, atLimit)).toEqual({
      ok: true,
      value: { question: DEFAULT_QUESTION, context: atLimit },
    });
    expect(validate(DEFAULT_QUESTION, "a".repeat(501))).toEqual({
      ok: false,
      errors: { context: "Use 500 characters or fewer for the context." },
    });
  });

  it("normalizes line endings and tabs", () => {
    const result = validate("Which\r\none\rtab\there", "line1\r\nline2\rc\td");
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.question).toBe("Which one tab here");
      expect(result.value.context).toBe("line1\nline2\nc d");
    }
  });

  it("flattens question newlines but preserves context paragraphs", () => {
    const result = validate("one\ntwo", "one\ntwo\n\nthree");
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.question).toBe("one two");
      expect(result.value.context).toBe("one\ntwo\n\nthree");
    }
  });

  it("rejects control characters", () => {
    for (const control of [
      "\u0000",
      "\u0001",
      "\u000b",
      "\u000c",
      "\u001f",
      "\u007f",
      "\u009f",
    ]) {
      expect(validate(`a${control}b`, null)).toEqual({
        ok: false,
        errors: { question: "Enter valid text for the question." },
      });
      expect(validate(DEFAULT_QUESTION, `a${control}b`)).toEqual({
        ok: false,
        errors: { context: "Enter valid text for the context." },
      });
    }
  });

  it("rejects control characters before trimming", () => {
    expect(validate("  \u0001  ", null)).toEqual({
      ok: false,
      errors: { question: "Enter valid text for the question." },
    });
  });

  it("trims the explicit whitespace set", () => {
    const result = validate("\u00a0hello\u3000", "\u2009world\u2028\u2029");
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.question).toBe("hello");
      expect(result.value.context).toBe("world");
    }
  });

  it("normalizes to NFC", () => {
    const result = validate("cafe\u0301", "nai\u0308ve");
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.question).toBe("caf\u00e9");
      expect(result.value.context).toBe("na\u00efve");
    }
  });

  it("counts astral and joined emoji by code point", () => {
    const result = validate(
      "\u{1f600}",
      "\u{1f468}\u200d\u{1f469}\u200d\u{1f467}",
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.question).toBe("\u{1f600}");
      expect(countCodePoints(result.value.question)).toBe(1);
      expect(countCodePoints(result.value.context ?? "")).toBe(5);
    }
  });

  it("preserves RTL text", () => {
    const raw =
      "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645";
    const result = validate(raw, raw);
    expect(result).toEqual({
      ok: true,
      value: { question: raw, context: raw },
    });
  });

  it("rejects lone surrogates", () => {
    expect(validate("a\ud800b", null)).toEqual({
      ok: false,
      errors: { question: "Enter valid text for the question." },
    });
    expect(validate(DEFAULT_QUESTION, "a\udfffb")).toEqual({
      ok: false,
      errors: { context: "Enter valid text for the context." },
    });
  });

  it("preserves internal spaces and paragraphs", () => {
    const result = validate("two  spaces", "first\n\nsecond");
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.question).toBe("two  spaces");
      expect(result.value.context).toBe("first\n\nsecond");
    }
  });

  it("revalidates normalized output idempotently", () => {
    const result = validate(
      "  Which one\r\nshould I post?\t ",
      "  some\ncontext\t here  ",
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      const again = validate(result.value.question, result.value.context);
      expect(again).toEqual(result);
    }
  });

  it("collects both field errors", () => {
    expect(validate("", "a".repeat(501))).toEqual({
      ok: false,
      errors: {
        question: "Enter a question.",
        context: "Use 500 characters or fewer for the context.",
      },
    });
  });

  it("uses the configured limits when they change", () => {
    const result = validateConsultationText("abc", "d", {
      questionMax: 2,
      contextMax: 500,
    });
    expect(result).toEqual({
      ok: false,
      errors: { question: "Use 2 characters or fewer for the question." },
    });
  });
});

import re
import unicodedata
from dataclasses import dataclass

DEFAULT_QUESTION = "Which photos should I post?"

_TRIM_CHARS = (
    "\t\n\v\f\r"
    " "
    "\u0085"
    "\u00a0"
    "\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029"
    "\u202f"
    "\u205f"
    "\u3000"
)

_CONTROL_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


@dataclass(frozen=True)
class ConsultationText:
    question: str
    context: str | None


def _has_surrogates(value: str) -> bool:
    return any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def _normalize_field(raw: str, *, preserve_newlines: bool) -> str | None:
    if _has_surrogates(raw):
        return None
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFC", text)
    if preserve_newlines:
        text = text.replace("\t", " ")
        if _CONTROL_RE.search(text):
            return None
    else:
        text = text.replace("\n", " ").replace("\t", " ")
        if _CONTROL_RE.search(text):
            return None
    return text.strip(_TRIM_CHARS)


def validate_question(value: object, maximum: int) -> tuple[str | None, str | None]:
    """Return (normalized question, error). A missing or empty question is invalid."""
    if value is None:
        return None, "Enter a question."
    if not isinstance(value, str):
        return None, "Enter valid text for the question."
    normalized = _normalize_field(value, preserve_newlines=False)
    if normalized is None:
        return None, "Enter valid text for the question."
    if len(normalized) == 0:
        return None, "Enter a question."
    if len(normalized) > maximum:
        return None, f"Use {maximum} characters or fewer for the question."
    return normalized, None


def validate_context(value: object, maximum: int) -> tuple[str | None, str | None]:
    """Return (normalized context, error). Absent or empty context normalizes to None."""
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, "Enter valid text for the context."
    normalized = _normalize_field(value, preserve_newlines=True)
    if normalized is None:
        return None, "Enter valid text for the context."
    if len(normalized) > maximum:
        return None, f"Use {maximum} characters or fewer for the context."
    if normalized == "":
        return None, None
    return normalized, None


def validate_consultation_text(
    question: object,
    context: object,
    *,
    question_max: int,
    context_max: int,
) -> tuple[ConsultationText | None, dict[str, str]]:
    """Validate question and context together, returning normalized text or field errors."""
    normalized_question, question_error = validate_question(question, question_max)
    normalized_context, context_error = validate_context(context, context_max)

    errors: dict[str, str] = {}
    if question_error is not None:
        errors["question"] = question_error
    if context_error is not None:
        errors["context"] = context_error
    if errors:
        return None, errors

    assert normalized_question is not None
    return ConsultationText(question=normalized_question, context=normalized_context), {}

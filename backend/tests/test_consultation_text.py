import pytest
from pydantic import ValidationError

from app.consultation_text import (
    DEFAULT_QUESTION,
    ConsultationText,
    validate_consultation_text,
    validate_context,
    validate_question,
)
from app.schemas import ConsultationTextRequest

QUESTION_MAX = 120
CONTEXT_MAX = 500


def _validate(question: object, context: object):
    return validate_consultation_text(
        question,
        context,
        question_max=QUESTION_MAX,
        context_max=CONTEXT_MAX,
    )


def test_default_question_is_27_code_points() -> None:
    assert DEFAULT_QUESTION == "Which photos should I post?"
    assert len(DEFAULT_QUESTION) == 27


def test_default_question_is_valid() -> None:
    value, errors = _validate(DEFAULT_QUESTION, None)

    assert errors == {}
    assert value == ConsultationText(question=DEFAULT_QUESTION, context=None)


def test_empty_and_whitespace_question_is_rejected() -> None:
    for raw in ("", "   ", "\t", "\u00a0\u3000"):
        _, errors = _validate(raw, None)
        assert errors == {"question": "Enter a question."}


def test_missing_and_non_string_question_is_rejected() -> None:
    for raw in (None, 123, 1.5, True, ["x"], {"q": "a"}):
        _, errors = _validate(raw, None)
        assert "question" in errors
        assert errors["question"] in (
            "Enter a question.",
            "Enter valid text for the question.",
        )


def test_invalid_question_type_message() -> None:
    _, errors = _validate(123, None)
    assert errors == {"question": "Enter valid text for the question."}


def test_null_and_empty_context_are_absent() -> None:
    for raw in (None, "", "   ", "\n\t"):
        value, errors = _validate(DEFAULT_QUESTION, raw)
        assert errors == {}
        assert value is not None and value.context is None


def test_invalid_context_type_message() -> None:
    _, errors = _validate(DEFAULT_QUESTION, 123)
    assert errors == {"context": "Enter valid text for the context."}


def test_question_overflow_at_boundary() -> None:
    at_limit = "a" * QUESTION_MAX
    value, errors = _validate(at_limit, None)
    assert errors == {}
    assert value is not None and value.question == at_limit

    _, errors = _validate("a" * (QUESTION_MAX + 1), None)
    assert errors == {"question": f"Use {QUESTION_MAX} characters or fewer for the question."}


def test_context_overflow_at_boundary() -> None:
    at_limit = "a" * CONTEXT_MAX
    value, errors = _validate(DEFAULT_QUESTION, at_limit)
    assert errors == {}
    assert value is not None and value.context == at_limit

    _, errors = _validate(DEFAULT_QUESTION, "a" * (CONTEXT_MAX + 1))
    assert errors == {"context": f"Use {CONTEXT_MAX} characters or fewer for the context."}


def test_line_endings_and_tabs_are_normalized() -> None:
    value, errors = _validate("Which\r\none\rtab\there", "line1\r\nline2\rc\td")
    assert errors == {}

    assert value is not None
    assert value.question == "Which one tab here"
    assert value.context == "line1\nline2\nc d"


def test_question_flattens_newlines_but_context_preserves_them() -> None:
    value, errors = _validate("one\ntwo", "one\ntwo\n\nthree")
    assert errors == {}
    assert value is not None
    assert value.question == "one two"
    assert value.context == "one\ntwo\n\nthree"


def test_control_characters_are_rejected() -> None:
    for control in ("\x00", "\x01", "\x0b", "\x0c", "\x1f", "\x7f", "\x9f"):
        _, errors = _validate(f"a{control}b", None)
        assert errors == {"question": "Enter valid text for the question."}

        _, errors = _validate(DEFAULT_QUESTION, f"a{control}b")
        assert errors == {"context": "Enter valid text for the context."}


def test_control_character_before_trimming_is_rejected() -> None:
    _, errors = _validate("  \x01  ", None)
    assert errors == {"question": "Enter valid text for the question."}


def test_explicit_whitespace_is_trimmed() -> None:
    value, errors = _validate("\u00a0hello\u3000", "\u2009world\u2028\u2029")
    assert errors == {}
    assert value is not None
    assert value.question == "hello"
    assert value.context == "world"


def test_nfc_normalization_is_applied() -> None:
    value, errors = _validate("cafe\u0301", "nai\u0308ve")
    assert errors == {}
    assert value is not None
    assert value.question == "caf\u00e9"
    assert value.context == "na\u00efve"


def test_astral_and_joined_emoji_are_counted_by_code_point() -> None:
    value, errors = _validate("\U0001f600", "\U0001f468\u200d\U0001f469\u200d\U0001f467")
    assert errors == {}
    assert value is not None
    assert value.question == "\U0001f600"
    assert len(value.question) == 1
    assert len(value.context or "") == 5


def test_rtl_text_is_preserved() -> None:
    raw = "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645"
    value, errors = _validate(raw, raw)
    assert errors == {}
    assert value is not None
    assert value.question == raw
    assert value.context == raw


def test_lone_surrogates_are_rejected() -> None:
    _, errors = _validate("a\ud800b", None)
    assert errors == {"question": "Enter valid text for the question."}

    _, errors = _validate(DEFAULT_QUESTION, "a\udfffb")
    assert errors == {"context": "Enter valid text for the context."}


def test_internal_spaces_and_paragraphs_are_preserved() -> None:
    value, errors = _validate("two  spaces", "first\n\nsecond")
    assert errors == {}
    assert value is not None
    assert value.question == "two  spaces"
    assert value.context == "first\n\nsecond"


def test_normalized_output_is_idempotent() -> None:
    value, errors = _validate("  Which one\r\nshould I post?\t ", "  some\ncontext\t here  ")
    assert errors == {}
    assert value is not None

    again, again_errors = _validate(value.question, value.context)
    assert again_errors == {}
    assert again == value


def test_collects_both_field_errors() -> None:
    _, errors = _validate("", "a" * (CONTEXT_MAX + 1))
    assert errors == {
        "question": "Enter a question.",
        "context": f"Use {CONTEXT_MAX} characters or fewer for the context.",
    }


def test_validators_are_reusable_individually() -> None:
    assert validate_question(None, QUESTION_MAX) == (None, "Enter a question.")
    assert validate_question(" hi ", QUESTION_MAX) == ("hi", None)
    assert validate_context(None, CONTEXT_MAX) == (None, None)
    assert validate_context(" hi ", CONTEXT_MAX) == ("hi", None)


def test_schema_rejects_empty_question_with_exact_message() -> None:
    with pytest.raises(ValidationError) as exc:
        ConsultationTextRequest.model_validate({"question": "", "context": None})

    errors = exc.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("question",)
    assert errors[0]["msg"] == "Enter a question."


def test_schema_rejects_missing_question_with_exact_message() -> None:
    with pytest.raises(ValidationError) as exc:
        ConsultationTextRequest.model_validate({"context": None})

    errors = exc.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("question",)
    assert errors[0]["msg"] == "Enter a question."


def test_schema_rejects_non_string_question_with_exact_message() -> None:
    with pytest.raises(ValidationError) as exc:
        ConsultationTextRequest.model_validate({"question": 123, "context": None})

    assert exc.value.errors()[0]["loc"] == ("question",)
    assert exc.value.errors()[0]["msg"] == "Enter valid text for the question."


def test_schema_normalizes_valid_text_and_absent_context() -> None:
    request = ConsultationTextRequest.model_validate(
        {"question": "  Which one?  ", "context": None}
    )

    assert request.question == "Which one?"
    assert request.context is None


def test_schema_turns_empty_context_into_none() -> None:
    request = ConsultationTextRequest.model_validate({"question": "Which one?", "context": "   "})

    assert request.question == "Which one?"
    assert request.context is None

import uuid
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.audience import Audience, validate_audience
from app.config import get_settings
from app.consultation_text import validate_context, validate_question
from app.private_link import parse_generation
from app.validation import validate_alias, validate_email, validate_password


class AccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    alias: str
    password: str

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        return validate_email(value)

    @field_validator("alias")
    @classmethod
    def _check_alias(cls, value: str) -> str:
        display, _ = validate_alias(value)
        return display

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password(value)


class SignInRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        return validate_email(value)


class AccountSummary(BaseModel):
    id: str
    alias: str


class SessionResponse(BaseModel):
    authenticated: Literal[True]
    account: AccountSummary


class ProfileResponse(BaseModel):
    email: str
    nickname: str


class ApplicationConfigResponse(BaseModel):
    consultation_min_photos: int
    consultation_max_photos: int
    max_open_consultations: int
    photo_max_input_bytes: int
    consultation_question_max_length: int
    consultation_context_max_length: int


class ConsultationAudienceRequest(BaseModel):
    """Reusable strict audience contract for the future publication request (RF-10)."""

    model_config = ConfigDict(extra="forbid")

    audience: Audience

    @model_validator(mode="before")
    @classmethod
    def _missing_audience_as_field_error(cls, value: object) -> object:
        if isinstance(value, dict) and "audience" not in value:
            return {**value, "audience": None}
        return value

    @field_validator("audience", mode="before")
    @classmethod
    def _check_audience(cls, value: object) -> Audience:
        audience, error = validate_audience(value)
        if error is not None:
            raise PydanticCustomError("consultation_audience", error)
        assert audience is not None
        return audience


class ConsultationTextRequest(BaseModel):
    """Reusable question/context contract for the future publication request (RF-10)."""

    model_config = ConfigDict(extra="forbid")

    question: str
    context: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _missing_question_as_field_error(cls, value: object) -> object:
        if isinstance(value, dict) and "question" not in value:
            return {**value, "question": None}
        return value

    @field_validator("question", mode="before")
    @classmethod
    def _check_question(cls, value: object) -> str:
        normalized, error = validate_question(
            value, get_settings().consultation_question_max_length
        )
        if error is not None:
            raise PydanticCustomError("consultation_question", error)
        assert normalized is not None
        return normalized

    @field_validator("context", mode="before")
    @classmethod
    def _check_context(cls, value: object) -> str | None:
        normalized, error = validate_context(value, get_settings().consultation_context_max_length)
        if error is not None:
            raise PydanticCustomError("consultation_context", error)
        return normalized


class UploadSessionResponse(BaseModel):
    id: str
    lease_expires_at: str


class UploadImageResponse(BaseModel):
    id: str
    width: int
    height: int


class ConsultationPublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: uuid.UUID
    ordered_image_ids: list[uuid.UUID]
    question: str
    context: str | None = None
    audience: Audience

    @model_validator(mode="before")
    @classmethod
    def _missing_fields_as_errors(cls, value: object) -> object:
        if isinstance(value, dict):
            result = dict(value)
            for field in ("question", "audience"):
                if field not in result:
                    result[field] = None
            return result
        return value

    @field_validator("question", mode="before")
    @classmethod
    def _check_question(cls, value: object) -> str:
        normalized, error = validate_question(
            value, get_settings().consultation_question_max_length
        )
        if error is not None:
            raise PydanticCustomError("consultation_question", error)
        assert normalized is not None
        return normalized

    @field_validator("context", mode="before")
    @classmethod
    def _check_context(cls, value: object) -> str | None:
        normalized, error = validate_context(value, get_settings().consultation_context_max_length)
        if error is not None:
            raise PydanticCustomError("consultation_context", error)
        return normalized

    @field_validator("audience", mode="before")
    @classmethod
    def _check_audience(cls, value: object) -> Audience:
        audience, error = validate_audience(value)
        if error is not None:
            raise PydanticCustomError("consultation_audience", error)
        assert audience is not None
        return audience


class ConsultationPublishedResponse(BaseModel):
    id: str
    state: Literal["open"]
    audience: str


class ConsultationCapacityResponse(BaseModel):
    open_count: int
    limit: int
    can_start: bool


class ConsultationPhotoResponse(BaseModel):
    id: str
    width: int
    height: int


class ConsultationDetailResponse(BaseModel):
    id: str
    owner_nickname: str
    question: str
    context: str | None
    audience: str
    state: Literal["open"]
    published_at: str
    photos: list[ConsultationPhotoResponse]


class OwnerLinkResponse(BaseModel):
    active: bool
    generation: str
    token: str | None


class ConsultationEntryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["owner", "reader"]


class MyConsultationOpenListItem(BaseModel):
    id: str
    state: Literal["open"]
    question: str
    audience: str
    published_at: str
    total_votes: int = Field(ge=0)


class ConsultationResultOptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    photo_id: str
    ordinal: int = Field(ge=0)
    vote_count: int = Field(ge=0)


class ConsultationResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consultation_id: str
    state: Literal["open"]
    total_votes: int = Field(ge=0)
    options: list[ConsultationResultOptionResponse]


class FinalizedOptionResponse(BaseModel):
    ordinal: int = Field(ge=0)
    vote_count: int = Field(ge=0)
    selected: bool


class FinalResultSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finalized_at: str
    total_votes: int = Field(ge=0)
    declaration: Literal["selected", "none"]
    selected_ordinals: list[int]
    options: list[FinalizedOptionResponse]


class MyConsultationFinalizedListItem(BaseModel):
    id: str
    state: Literal["finalized"]
    published_at: str
    result: FinalResultSummaryResponse | None


MyConsultationListItem = Annotated[
    Union[MyConsultationOpenListItem, MyConsultationFinalizedListItem],
    Field(discriminator="state"),
]


class MyConsultationListResponse(BaseModel):
    items: list[MyConsultationListItem]
    next_cursor: str | None


class MyConsultationOpenDetail(BaseModel):
    id: str
    state: Literal["open"]
    owner_nickname: str
    question: str
    context: str | None
    audience: str
    published_at: str
    photos: list[ConsultationPhotoResponse]


class MyConsultationFinalizedDetail(BaseModel):
    id: str
    state: Literal["finalized"]
    published_at: str
    result: FinalResultSummaryResponse | None


MyConsultationOwnerDetail = Annotated[
    Union[MyConsultationOpenDetail, MyConsultationFinalizedDetail],
    Field(discriminator="state"),
]


class LinkMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_generation: str

    @field_validator("expected_generation")
    @classmethod
    def _check_generation(cls, value: str) -> str:
        if parse_generation(value) is None:
            raise ValueError("Enter a valid link generation.")
        return value


class ConsultationDeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_state: Literal["open", "finalized"]


class FinalizationDeclarationRequest(BaseModel):
    """Strict tagged declaration: a selected set or an explicit none (RF-19/RF-20)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["selected", "none"]
    option_ids: list[uuid.UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_option_ids(self) -> "FinalizationDeclarationRequest":
        if self.kind == "none" and self.option_ids:
            raise ValueError("No options may be declared when the choice is none.")
        if self.kind == "selected" and not self.option_ids:
            raise ValueError("Select at least one option.")
        if self.kind == "selected" and len(set(self.option_ids)) != len(self.option_ids):
            raise ValueError("Options must be unique.")
        return self


class ConsultationFinalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: uuid.UUID
    expected_state: Literal["open"]
    declaration: FinalizationDeclarationRequest


class FeedPhotoResponse(BaseModel):
    id: str
    width: int
    height: int


class FeedItemResponse(BaseModel):
    id: str
    owner_nickname: str
    question: str
    context_excerpt: str | None
    audience: Literal["public"]
    state: Literal["open"]
    published_at: str
    is_owner: bool
    has_voted: bool
    first_photo: FeedPhotoResponse


class FeedResponse(BaseModel):
    items: list[FeedItemResponse]
    next_cursor: str | None


class VoteSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    photo_id: uuid.UUID


class VoteNotVotedResponse(BaseModel):
    status: Literal["not_voted"]


class VoteVotedResponse(BaseModel):
    status: Literal["voted"]
    photo_id: str


VoteStatusResponse = Annotated[
    Union[VoteNotVotedResponse, VoteVotedResponse],
    Field(discriminator="status"),
]

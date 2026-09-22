from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

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


class UploadSessionResponse(BaseModel):
    id: str
    lease_expires_at: str


class UploadImageResponse(BaseModel):
    id: str
    width: int
    height: int

"""Authentication & session contracts — SDD §2.6.1.4 (FR-AUTH / UC-01, UC-02)."""

import re
from enum import StrEnum
from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator


def _validate_and_normalize_email(value: str) -> str:
    """Normalize email to lowercase while permitting seeded `.local` domains."""
    stripped = value.strip()
    if "@" not in stripped:
        raise ValueError("value is not a valid email address: must contain @")
    local_part, _, domain = stripped.rpartition("@")
    try:
        if domain.lower().endswith(".local"):
            prefix = domain[:-6]
            if not prefix or prefix.startswith(".") or prefix.endswith("."):
                raise ValueError("value is not a valid email address: invalid .local domain")
            validated = validate_email(f"{local_part}@{prefix}.example", check_deliverability=False)
            return f"{validated.local_part}@{validated.domain[:-8]}.local".lower()
        validated = validate_email(stripped, check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc
    return validated.normalized.lower()


NormalizedEmail = Annotated[str, AfterValidator(_validate_and_normalize_email)]
"""Email lowercased before it ever reaches the database.

`EmailStr` only normalizes the domain, so 'Alice@corp.com' survives validation
unchanged and — because PostgreSQL string equality is case-sensitive — used to
produce a second account for the same mailbox, with login succeeding or failing
depending on the casing typed. Local-parts are technically case-sensitive per
RFC 5321, but no mail provider this product targets treats them that way, and
`users.email` is the identity key for login, invitations and password reset.
Paired with the `uq_users_email_lower` index in the database, which enforces
the same invariant for any writer that bypasses this contract.
"""

_PASSWORD_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[A-Z]"), "must contain at least one uppercase letter"),
    (re.compile(r"[a-z]"), "must contain at least one lowercase letter"),
    (re.compile(r"[0-9]"), "must contain at least one digit"),
    (re.compile(r"[^A-Za-z0-9]"), "must contain at least one special character"),
)


def _validate_password_complexity(password: str) -> str:
    """FR-AUTH-001 / UC-01 main flow + UC-01 E2 — kompleksitas & anti-DoS.

    UC-01 E2: menolak password > 128 karakter atau yang memuat null byte
    SEBELUM masuk ke hashing Argon2id (mencegah serangan DoS komputasi).
    Skor entropi zxcvbn (SRS UC-01 langkah 2) adalah pengecekan tambahan di
    domain service (FASE 3), bukan di lapisan kontrak data ini.
    """
    if "\0" in password:
        raise ValueError("Password must not contain null bytes")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters long")
    for pattern, message in _PASSWORD_RULES:
        if not pattern.search(password):
            raise ValueError(f"Password {message}")
    return password


def _validate_login_password(password: str) -> str:
    """F4-MED-22: batasi panjang password login & larang null byte untuk anti-DoS."""
    if "\0" in password:
        raise ValueError("Password must not contain null bytes")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters long")
    return password


class WorkspaceRole(StrEnum):
    """SDD §2.4.2 Tabel 3 `workspace_members.role` — SRS UC-01 step 4c & UC-05.

    NB: "Owner" di SRS/EC-03 adalah atribut kepemilikan workspace (siapa yang
    tidak boleh dihapus tanpa transfer ownership dulu), bukan nilai enum role
    yang berdiri sendiri — nilai role tetap 3: MANAGER, PENTESTER, VIEWER.
    """

    MANAGER = "MANAGER"
    PENTESTER = "PENTESTER"
    VIEWER = "VIEWER"


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail
    password: str
    full_name: str = Field(min_length=1, max_length=100)
    workspace_name: str = Field(min_length=1, max_length=150)
    invitation_token: str | None = Field(default=None, description="UC-01 alt 2a / EC-02")

    _validate_password = field_validator("password")(_validate_password_complexity)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail
    password: str = Field(max_length=128)
    totp_code: str | None = Field(default=None, pattern=r"^\d{6}$")

    _validate_password = field_validator("password")(_validate_login_password)


class UserDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: NormalizedEmail
    full_name: str
    is_superadmin: bool = False
    mfa_enabled: bool = False


class WorkspaceMembership(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    role: WorkspaceRole
    tier: str | None = None


class RegisterResponse(BaseModel):
    """201 Created — SDD §2.6.1.4 contoh respons registrasi."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    email: NormalizedEmail
    full_name: str
    workspace_id: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)


class TokenResponse(BaseModel):
    """200 OK — SDD §2.6.1.4 contoh respons login."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)
    user: UserDTO
    workspaces: list[WorkspaceMembership] = Field(default_factory=list)


class MeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: UserDTO
    workspaces: list[WorkspaceMembership] = Field(default_factory=list)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail


class ForgotPasswordResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=10, max_length=1000)
    new_password: str

    _validate_password = field_validator("new_password")(_validate_password_complexity)


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=1, max_length=128)


class MFASetupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    secret: str
    otpauth_uri: str
    enabled: bool


class MFAVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    totp_code: str = Field(pattern=r"^\d{6}$")

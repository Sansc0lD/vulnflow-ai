"""Authentication & session contracts — SDD §2.6.1.4 (FR-AUTH / UC-01, UC-02)."""

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_PASSWORD_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[A-Z]"), "harus memuat minimal satu huruf besar"),
    (re.compile(r"[a-z]"), "harus memuat minimal satu huruf kecil"),
    (re.compile(r"[0-9]"), "harus memuat minimal satu angka"),
    (re.compile(r"[^A-Za-z0-9]"), "harus memuat minimal satu karakter khusus"),
)


def _validate_password_complexity(password: str) -> str:
    """FR-AUTH-001 / UC-01 main flow + UC-01 E2 — kompleksitas & anti-DoS.

    UC-01 E2: menolak password > 128 karakter atau yang memuat null byte
    SEBELUM masuk ke hashing Argon2id (mencegah serangan DoS komputasi).
    Skor entropi zxcvbn (SRS UC-01 langkah 2) adalah pengecekan tambahan di
    domain service (FASE 3), bukan di lapisan kontrak data ini.
    """
    if "\0" in password:
        raise ValueError("kata sandi tidak boleh memuat karakter null byte")
    if len(password) < 8:
        raise ValueError("kata sandi minimal 8 karakter")
    if len(password) > 128:
        raise ValueError("kata sandi maksimal 128 karakter")
    for pattern, message in _PASSWORD_RULES:
        if not pattern.search(password):
            raise ValueError(f"kata sandi {message}")
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

    email: EmailStr
    password: str
    full_name: str = Field(min_length=1, max_length=100)
    workspace_name: str = Field(min_length=1, max_length=150)
    invitation_token: str | None = Field(default=None, description="UC-01 alt 2a / EC-02")

    _validate_password = field_validator("password")(_validate_password_complexity)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class UserDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: EmailStr
    full_name: str


class WorkspaceMembership(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    role: WorkspaceRole


class RegisterResponse(BaseModel):
    """201 Created — SDD §2.6.1.4 contoh respons registrasi."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    email: EmailStr
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

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.models.domain import UserRole
from app.schemas.pydantic_models import TokenData, UserProfile
from app.utils.errors import UnauthorizedError, ForbiddenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against PBKDF2-HMAC-SHA256 hashed string."""
    try:
        salt, expected_hash = hashed_password.split('$', 1)
        actual_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return secrets.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False

# Pre-computed secure hashes for demo users (PBKDF2-HMAC-SHA256 with fixed salt for deterministic demo setup)
_DEMO_SALT = "a1b2c3d4e5f60718"
_DEMO_PW_HASH = hash_password("password123", salt=_DEMO_SALT)

DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "officer1": {
        "user_id": "OFFICER-IND-1001",
        "username": "officer1",
        "hashed_password": _DEMO_PW_HASH,
        "role": UserRole.OFFICER,
        "full_name": "Inspector R. K. Sharma",
        "badge_number": "LM-DEL-4092"
    },
    "reviewer1": {
        "user_id": "REVIEWER-IND-2001",
        "username": "reviewer1",
        "hashed_password": _DEMO_PW_HASH,
        "role": UserRole.REVIEWER,
        "full_name": "Senior Officer A. Verma",
        "badge_number": "LM-DEL-1008"
    },
    "admin1": {
        "user_id": "ADMIN-IND-0001",
        "username": "admin1",
        "hashed_password": _DEMO_PW_HASH,
        "role": UserRole.ADMIN,
        "full_name": "System Administrator",
        "badge_number": "LM-SYS-0001"
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token with expiration timestamp."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> TokenData:
    """Decode and cryptographically validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        role_str: str = payload.get("role")
        if not user_id:
            raise UnauthorizedError("Invalid token payload: missing subject identifier.")
        role = UserRole(role_str) if role_str else UserRole.OFFICER
        return TokenData(user_id=user_id, role=role)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Authentication token has expired. Please login again.")
    except jwt.PyJWTError:
        raise UnauthorizedError("Could not validate credentials: token is malformed or invalid.")

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserProfile:
    """Extract and validate the authenticated user from Bearer token."""
    if not token:
        raise UnauthorizedError("Authentication required. Missing or empty Bearer token.")

    token_data = decode_access_token(token)
    for user_info in DEMO_USERS.values():
        if user_info["user_id"] == token_data.user_id:
            return UserProfile(
                user_id=user_info["user_id"],
                username=user_info["username"],
                role=user_info["role"],
                full_name=user_info["full_name"],
                badge_number=user_info.get("badge_number")
            )

    raise UnauthorizedError("User profile associated with token not found.")

class RequireRole:
    """Dependency for enforcing role-based access control."""
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenError(f"User role '{current_user.role.value}' is not authorized. Required: {[r.value for r in self.allowed_roles]}")
        return current_user

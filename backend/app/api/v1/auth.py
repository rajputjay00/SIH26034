from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.security import DEMO_USERS, create_access_token, get_current_user, verify_password
from app.schemas.pydantic_models import LoginRequest, Token, UserProfile
from app.utils.errors import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(request: LoginRequest):
    """Authenticate officer credentials using secure hash verification and return JWT access token."""
    user = DEMO_USERS.get(request.username)
    if not user or not verify_password(request.password, user.get("hashed_password", "")):
        raise UnauthorizedError("Invalid username or password.")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user["user_id"], "role": user["role"].value},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=UserProfile)
def get_authenticated_user(current_user: UserProfile = Depends(get_current_user)):
    """Retrieve profile details for currently authenticated officer."""
    return current_user

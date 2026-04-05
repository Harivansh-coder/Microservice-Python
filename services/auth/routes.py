# services/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import UserRegister, UserLogin, TokenResponse, TokenRefresh, UserResponse, TokenData
from models import User, RefreshToken, SessionLocal
from dependencies import get_db, verify_jwt, get_current_user
from utils import verify_password, get_password_hash, create_access_token, create_refresh_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered: {user.username}")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens"""
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")

    # Create tokens
    access_token = create_access_token({
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    })
    refresh_token = create_refresh_token(user.id, db)

    logger.info(f"User logged in: {user.username}")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    refresh = db.query(RefreshToken).filter(
        RefreshToken.token == token_data.refresh_token,
        RefreshToken.is_revoked == False
    ).first()

    if not refresh or refresh.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == refresh.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401, detail="User not found or inactive")

    # Create new access token
    access_token = create_access_token({
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    })

    return TokenResponse(access_token=access_token, refresh_token=refresh.token)


@router.post("/logout")
async def logout(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Revoke refresh token"""
    refresh = db.query(RefreshToken).filter(
        RefreshToken.token == token_data.refresh_token).first()
    if refresh:
        refresh.is_revoked = True
        db.commit()
        logger.info(f"User logged out: {refresh.user_id}")
    return {"message": "Logged out successfully"}


@router.get("/verify", response_model=TokenData)
async def verify_token_endpoint(token_data: TokenData = Depends(verify_jwt)):
    """Verify JWT token (used by API Gateway)"""
    return token_data


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

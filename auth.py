"""
Authentication module for GeoGenie API.
Supports HTTP Basic Auth and JWT tokens.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from db import SessionLocal
import crud
import secrets
import os

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# Security schemes
http_basic = HTTPBasic()
http_bearer = HTTPBearer()

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# No in-memory users: users are persisted in the SQLite database via CRUD helpers.


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        User dict if authenticated, None otherwise
    """
    db: Session = SessionLocal()
    try:
        db_user = crud.get_user_by_username(db, username)
        if not db_user:
            return None
        if getattr(db_user, "disabled", False):
            return None
        if not verify_password(password, db_user.hashed_password):
            return None
        return {"username": db_user.username}
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None


def get_current_user_basic(credentials: HTTPBasicCredentials = Depends(http_basic)) -> dict:
    """
    Dependency for HTTP Basic Authentication.
    
    Args:
        credentials: HTTP Basic credentials
        
    Returns:
        Authenticated user dict
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> dict:
    """
    Dependency for JWT Bearer Token Authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Authenticated user dict
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    db: Session = SessionLocal()
    try:
        db_user = crud.get_user_by_username(db, username)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username}
    finally:
        db.close()


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Optional authentication - returns user if token is valid, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None
    return get_current_user_token(credentials)


# Convenience function to use either basic or token auth
def get_current_user(
    token_credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    basic_credentials: Optional[HTTPBasicCredentials] = Depends(HTTPBasic(auto_error=False))
) -> dict:
    """
    Flexible authentication that accepts either Basic Auth or Bearer Token.
    Tries Bearer token first, then falls back to Basic Auth.
    """
    # Try Bearer token first
    if token_credentials:
        try:
            return get_current_user_token(token_credentials)
        except HTTPException:
            pass
    
    # Fall back to Basic Auth (if provided)
    if basic_credentials:
        try:
            return get_current_user_basic(basic_credentials)
        except HTTPException:
            pass
    
    # If neither works, raise error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Use Basic Auth or Bearer Token.",
        headers={"WWW-Authenticate": "Basic, Bearer"},
    )


def add_user(username: str, password: str) -> dict:
    """Add a new user to the in-memory USERS_DB.

    Returns the created user dict (without password) or raises HTTPException on error.
    Note: This is an in-memory store; in production persist to a database.
    """
    # If user exists in DB, reject
    db: Session = SessionLocal()
    try:
        if crud.get_user_by_username(db, username):
            raise HTTPException(status_code=400, detail="User already exists")
        user = crud.create_user(db, username, password)
        return {"username": user.username}
    finally:
        db.close()


"""Sign-up, login and the logged-in-user check."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import JWT_TOKEN
from .database import get_db
from .models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

TOKEN_HOURS = 24


class SignupIn(BaseModel):
    email: str
    password: str
    name: str


class LoginIn(BaseModel):
    email: str
    password: str


# ---------- helpers

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def make_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": expires}, JWT_TOKEN, algorithm="HS256")


def user_json(user: User) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name}


# ---------- protected-route dependency

COOKIE_NAME = "access_token"


def set_login_cookie(response: Response, token: str):
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax", max_age=TOKEN_HOURS * 3600)


def get_current_user(
    authorization: str | None = Header(None),
    access_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User:
    """Use as `user: User = Depends(get_current_user)` on any route that needs login.
    Accepts the login cookie (browser) or an `Authorization: Bearer` header (Postman, tests)."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
    elif access_token:
        token = access_token
    else:
        raise HTTPException(status_code=401, detail="Not logged in")

    try:
        user_id = int(jwt.decode(token, JWT_TOKEN, algorithms=["HS256"])["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------- routes

@router.post("/signup", status_code=201)
def signup(data: SignupIn, response: Response, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Enter a valid email")
    if len(data.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=email, password_hash=hash_password(data.password), name=data.name)
    db.add(user)
    db.commit()
    token = make_token(user.id)
    set_login_cookie(response, token)
    return {"token": token, "user": user_json(user)}


@router.post("/login")
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.strip().lower()))
    if user is None or not check_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    token = make_token(user.id)
    set_login_cookie(response, token)
    return {"token": token, "user": user_json(user)}


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    """Small protected route: returns whoever the token belongs to."""
    return user_json(user)

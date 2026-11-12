from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.deps import get_current_user
from app.schemas import RegisterRequest, TokenResponse, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db=Depends(get_db)):
    """Self-registration always creates an *employee*. Admins are created by seeding/DB only."""
    username = body.username.lower()
    if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        raise HTTPException(status_code=409, detail="Username already taken")
    cur = db.execute(
        "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, 'employee')",
        (username, hash_password(body.password), body.full_name.strip()),
    )
    db.execute("INSERT INTO leave_balances (user_id) VALUES (?)", (cur.lastrowid,))
    db.commit()
    return TokenResponse(
        access_token=create_access_token(cur.lastrowid),
        role="employee",
        full_name=body.full_name.strip(),
    )


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    row = db.execute(
        "SELECT * FROM users WHERE username = ?", (form.username.lower(),)
    ).fetchone()
    if not row or not verify_password(form.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(row["id"]),
        role=row["role"],
        full_name=row["full_name"],
    )


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return user

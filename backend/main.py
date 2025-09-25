from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# SECRET for demo only
SECRET_KEY = "demo-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

engine = create_engine('sqlite:///./app.db', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Cloud Campus Core - Minimal")

# --- DB models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # student|teacher|admin

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    marked_by = Column(Integer, ForeignKey('users.id'))
    date = Column(String, default=datetime.utcnow().isoformat())
    status = Column(String)  # present/absent
    note = Column(Text, nullable=True)

class Marks(Base):
    __tablename__ = "marks"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String)
    marks = Column(Integer)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- Pydantic schemas ---
class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Utility functions ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def role_required(required_roles):
    def wrapper(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return current_user
    return wrapper

# --- Routes ---
@app.post("/users/register", tags=["auth"])
def register(user: UserCreate, db: SessionLocal = Depends(get_db)):
    if user.role not in ("student","teacher","admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = User(username=user.username, full_name=user.full_name or "", hashed_password=get_password_hash(user.password), role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "user created", "user_id": db_user.id}

@app.post("/token", response_model=Token, tags=["auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# student views own attendance
@app.get("/attendance/student/{student_id}", tags=["attendance"])
def view_attendance(student_id: int, current_user: User = Depends(role_required(["student","teacher","admin"])), db: SessionLocal = Depends(get_db)):
    # students can only view their own unless teacher/admin
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Not permitted to view others' attendance")
    rows = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    return [{"id":r.id,"student_id":r.student_id,"marked_by":r.marked_by,"date":r.date,"status":r.status,"note":r.note} for r in rows]

# teacher marks attendance
@app.post("/attendance/mark", tags=["attendance"])
def mark_attendance(student_id: int, status: str, note: Optional[str] = None, current_user: User = Depends(role_required(["teacher","admin"])), db: SessionLocal = Depends(get_db)):
    att = Attendance(student_id=student_id, marked_by=current_user.id, status=status, note=note)
    db.add(att)
    db.commit()
    db.refresh(att)
    return {"msg":"marked", "attendance_id": att.id}

# view marks
@app.get("/marks/student/{student_id}", tags=["marks"])
def view_marks(student_id: int, current_user: User = Depends(role_required(["student","teacher","admin"])), db: SessionLocal = Depends(get_db)):
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Not permitted to view others' marks")
    rows = db.query(Marks).filter(Marks.student_id == student_id).all()
    return [{"id":r.id,"subject":r.subject,"marks":r.marks,"uploaded_by":r.uploaded_by,"uploaded_at":r.uploaded_at.isoformat()} for r in rows]

# teacher uploads marks
@app.post("/marks/upload", tags=["marks"])
def upload_marks(student_id: int, subject: str, marks: int, current_user: User = Depends(role_required(["teacher","admin"])), db: SessionLocal = Depends(get_db)):
    m = Marks(student_id=student_id, subject=subject, marks=marks, uploaded_by=current_user.id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"msg":"marks uploaded", "marks_id": m.id}

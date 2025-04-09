from pydantic import BaseModel
from typing import Annotated, Optional
from contextlib import asynccontextmanager

from jose import JWTError, jwt

from fastapi import FastAPI, APIRouter, Form, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import Header
from fastapi.responses import RedirectResponse

from sqlalchemy import Engine, create_engine, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from src.usr_model import User
from src.event_model import Events
from src.hasher import Hasher
from src.auth import create_access_token, decode_access_token
from src.config import SECRET_KEY, ALGORITHM
from src.usr_model import Base as UserBase
from src.startup import create_admin_user



@asynccontextmanager
async def lifespan(app: FastAPI):
    db: Session = SessionLocal()
    try:
        create_admin_user(db)
    finally:
        db.close()
    yield
        
        
router = APIRouter()

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
USER_DATABASE_URL = "sqlite:///./user_database.db"
EVENT_DATABASE_URL = "sqlite:///./event_database.db"

engine_usr = create_engine(USER_DATABASE_URL, connect_args={"check_same_thread": False})
engine_event = create_engine(EVENT_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False)
SessionLocal.configure(binds={User: engine_usr, Events: engine_event})

# OAUTH Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create both databases.
# This now creates the user tables using UserBase on engine_usr
# and the events table using the Events model on engine_event.
UserBase.metadata.create_all(bind=engine_usr)
Events.metadata.create_all(bind=engine_event)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_token_optional(authorization: str = Header(default=None)):
    if not authorization:
        return None
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        return None
    return token


def get_current_user(request: Request, db: Session = Depends(get_session)):
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    return db.query(User).filter(User.uid == int(user_id)).first()

# -----------------------------
# Home Page
# -----------------------------
@router.get("/")
def get(session: Session = Depends(get_session), current_user: Optional[User] = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}!"}

@app.get("/", response_class=HTMLResponse)
def main(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    return templates.TemplateResponse('home.html', {
        'request': request,
        'username': current_user.username if current_user else None
    })

# -----------------------------
# LOGIN AND REGISTRATION
# -----------------------------
@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/register")
def register_user(
    new_username: str = Form(...),
    new_password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_session)
):
    existing_user = db.query(User).filter(User.username == new_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_pw = Hasher.get_password_hash(new_password)

    new_user = User(
        username=new_username,
        email=email,
        password_hashed=hashed_pw,
        first_name="New",
        last_name="User",
        about=""
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.uid)})

    response = JSONResponse(content={"message": "Registration successful"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
        samesite="lax"
    )
    return response

@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not Hasher.verify_password(form_data.password, user.password_hashed):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.uid)})

    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,  # 30 minutes
        samesite="lax"
    )
    return response

@app.post("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

# -----------------------------
# Profile Settings
# -----------------------------
@app.get("/profile/home", response_class=HTMLResponse)
def prof_main(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    if current_user is None:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse("profile_home.html", {
        "request": request,
        "username": current_user.username
    })

@app.get("/profile/security")
def prof_password(request: Request):
    return templates.TemplateResponse("profile_password.html", {"request": request})

@app.post("/profile/security")
def update_profile_settings(
    username: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_session)
):
    # Check if user exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create new user
    new_user = User(username=username, email=email, password=password)
    db.add(new_user)
    db.commit()
    return {"message": "Profile updated successfully!", "username": username}


@app.get("/profile/events", response_class=HTMLResponse)
def prof_events(request: Request, db: Session = Depends(get_session)):
    # Querying all events from the events database using the Events model
    events = db.query(Events).all()
    return templates.TemplateResponse("profile_events.html", {"request": request, "events": events})

@app.get("/profile/edit")
def prof_edit(request: Request):
    return templates.TemplateResponse("profile_edit.html", {"request": request})

@app.get("/profile/calendar")
def prof_calendar():
    return

# GET endpoint to render the Create Event form
@app.get("/organizer/create_event", response_class=HTMLResponse)
def get_create_event(request: Request):
    return templates.TemplateResponse("create_event.html", {"request": request})

@app.post("/organizer/create_event")
def post_create_event(
    title: str = Form(...),
    description: str = Form(None),
    event_date: str = Form(None),
    db: Session = Depends(get_session)
):
    """
    1) Create a new event in the database
    2) Append the event info to created_events.txt
    3) Redirect to /profile/events
    """
    # 1) Insert event into DB
    new_event = Events(
        title=title,
        description=description,
        event_date=event_date
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # 2) Write details to text file
    with open("created_events.txt", "a", encoding="utf-8") as f:
        f.write(f"Title: {title}\n")
        f.write(f"Description: {description}\n")
        f.write(f"Date: {event_date}\n")
        f.write("----------\n")

    # 3) Redirect to /profile/events
    return RedirectResponse(url="/profile/events", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/organizer/delete_event")
def org_del_event():
    return


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

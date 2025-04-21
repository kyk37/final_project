import os
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
from fastapi import File, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Query

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.session import get_user_session, get_event_session


from src.usr_model import User as UserBase
from src.event_model import Events as EventBase
from src.hasher import Hasher
from src.auth import create_access_token, decode_access_token
from src.config import SECRET_KEY, ALGORITHM
from src.startup import create_startup_users, create_events

from calendar_router import calendar_router

from datetime import date

from db.base import Base

# Database setup
USER_DATABASE_URL = "sqlite:///./user_database.db"


# File paths for the SQLite databases
USER_DB_FILE = "./user_database.db"

engine_usr = create_engine(USER_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal_usr = sessionmaker(autocommit=False, autoflush=False, bind=engine_usr)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Delete existing database files if they exist
    if os.path.exists(USER_DB_FILE):
        os.remove(USER_DB_FILE)

    # Create tables
    Base.metadata.create_all(bind=engine_usr)


    # Initialize database sessions
    db = SessionLocal_usr()
    try:
        organizer_map = create_startup_users(db)
        create_events(db, organizer_map)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()
    yield


# OAuth Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Setup APIRouter
router = APIRouter()
# Setup FastAPI
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(calendar_router)

async def get_token_optional(authorization: str = Header(default=None)):
    if not authorization:
        return None
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        return None
    return token

def get_current_user(request: Request, db: Session = Depends(get_user_session)):
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

    return db.query(UserBase).filter(UserBase.uid == int(user_id)).first()

# -----------------------------
# Home Page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def main(
    request: Request, 
    db_event: Session = Depends(get_event_session), 
    current_user: Optional[UserBase] = Depends(get_current_user),
    page: int = 1,
    per_page: int = 20
):
    '''
        Main Home Page
    '''
    from datetime import timedelta

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    events_this_week = []
    joined_event_ids = set()

    if current_user:
        user_in_event_db = db_event.merge(current_user)
        events_this_week = db_event.query(EventBase).filter(
            EventBase.owner_uid == current_user.uid,
            EventBase.date.between(start_of_week, end_of_week)
        ).all()
        joined_event_ids = {e.uid for e in user_in_event_db.events}
    
    # Search all Events that are NOT archived
    query = db_event.query(EventBase).filter(EventBase.archived == False)
    all_events = query.offset((page - 1) * per_page).limit(per_page).all()
    attendee_counts = {event.uid: len(event.attendees) for event in all_events}
    event_titles = {event.uid: (event.title) for event in all_events}
    
    total_events = query.count()
    total_pages = (total_events + per_page - 1) // per_page

    return templates.TemplateResponse('home.html', {
        'request': request,
        'username': current_user.username if current_user else None,
        'events_today': events_this_week,
        'all_events': all_events,
        'page': page,
        'total_pages': total_pages,
        'joined_event_ids': joined_event_ids,
        'attendee_counts': attendee_counts,
        'event_title': event_titles
    })


@app.get("/api/event/{event_id}")
def get_event_summary(
    event_id: int,
    db: Session = Depends(get_event_session),
    current_user: UserBase = Depends(get_current_user)
):
    event = db.query(EventBase).filter(EventBase.uid == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "title": event.title,
        "event_type": event.event_type,
        "tags": event.tags,
        "organizer": event.organizer,
        "date": event.date.strftime("%B %d, %Y"),
        "start_time": event.start_time.strftime("%I:%M %p"),
        "end_time": event.end_time.strftime("%I:%M %p"),
        "location": event.location,
        "description": event.description,
        "image_urls": event.image_urls
    }

@app.post("/api/join_event/{event_id}")
def join_event(
    event_id: int,
    db: Session = Depends(get_event_session),
    current_user: UserBase = Depends(get_current_user)
):
    '''
        Join an event from main page
    '''
    if current_user is None:
        raise HTTPException(status_code=401, detail="User must be logged in to join events")

    event = db.query(EventBase).filter(EventBase.uid == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user_in_event_db = db.merge(current_user)  # Attach user to current DB session

    if user_in_event_db not in event.attendees:
        event.attendees.append(user_in_event_db)
        db.commit()
        
    else:
        raise HTTPException(status_code=400, detail="Already joined this event")

    return {"message": "Successfully joined event"}



@app.post("/api/unjoin_event/{event_id}")
def unjoin_event(
    event_id: int,
    db: Session = Depends(get_event_session),
    current_user: UserBase = Depends(get_current_user)
):
    '''
        Leave Event
    '''
    if current_user is None:
        raise HTTPException(status_code=401, detail="User must be logged in")

    event = db.query(EventBase).filter(EventBase.uid == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user_in_event_db = db.merge(current_user)

    if user_in_event_db in event.attendees:
        event.attendees.remove(user_in_event_db)
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="Not joined to begin with")

    return {"message": "Successfully unjoined event"}



# -----------------------------
# Search Bar On home
# -----------------------------

@app.get("/search", response_class=HTMLResponse)
def search_events(
    request: Request,
    search: Optional[str] = "",
    db_event: Session = Depends(get_event_session),
    current_user: Optional[UserBase] = Depends(get_current_user),
    page: int = 1,
    per_page: int = 20
):
    from datetime import timedelta
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    events_this_week = []
    joined_event_ids = set()

    if current_user:
        user_in_event_db = db_event.merge(current_user)
        events_this_week = db_event.query(EventBase).filter(
            EventBase.owner_uid == current_user.uid,
            EventBase.date.between(start_of_week, end_of_week)
        ).all()
        joined_event_ids = {e.uid for e in user_in_event_db.events}

    base_query = db_event.query(EventBase).filter(EventBase.archived == False)

    if search:
        base_query = base_query.filter(
            EventBase.title.ilike(f"%{search}%") |
            EventBase.description.ilike(f"%{search}%") |
            EventBase.tags.ilike(f"%{search}%")
        )

    all_events = base_query.offset((page - 1) * per_page).limit(per_page).all()
    attendee_counts = {event.uid: len(event.attendees) for event in all_events}
    event_titles = {event.uid: (event.title) for event in all_events}
    total_events = base_query.count()
    total_pages = (total_events + per_page - 1) // per_page

    return templates.TemplateResponse("home.html", {
        "request": request,
        "username": current_user.username if current_user else None,
        "events_today": events_this_week,
        "all_events": all_events,
        "page": page,
        "total_pages": total_pages,
        "joined_event_ids": joined_event_ids,
        "attendee_counts": attendee_counts,
        "event_title": event_titles
    })
    
# -----------------------------
# LOGIN AND REGISTRATION
# -----------------------------
@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    message = request.cookies.get("message")
    response = templates.TemplateResponse("login.html", {"request": request, "message": message})
    response.delete_cookie("message")
    return response


@app.post("/register")
def register_user(
    new_username: str = Form(...),
    new_password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_user_session)
):
    existing_user = db.query(UserBase).filter(UserBase.username == new_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_pw = Hasher.get_password_hash(new_password)

    new_user = UserBase(
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
    db: Session = Depends(get_user_session)
):
    user = db.query(UserBase).filter(UserBase.username == form_data.username).first()
    if not user or not Hasher.verify_password(form_data.password, user.password_hashed):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.uid)})

    response = JSONResponse(content={"access_token": access_token})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
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
def prof_main(request: Request, current_user: Optional[UserBase] = Depends(get_current_user)):
    '''
        Profile Homepage
    '''

    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 10)
        return response
        
    cookie_msg = request.cookies.get("not_organizer_alert")

    response = templates.TemplateResponse("profile_home.html", {
        "request": request,
        "username": current_user.username,
        "profile_image_url": current_user.profile_image_url,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "about": current_user.about,
        "email": current_user.email,
        "is_organizer": current_user.is_organizer,
        "no_org": cookie_msg,
        "age": current_user.age,
        "phone": current_user.phone,
        "address": current_user.address
    })

    if cookie_msg:
        response.delete_cookie("not_organizer_alert")

    return response

@app.get("/profile/security")
def prof_password(request: Request, current_user: Optional[UserBase] = Depends(get_current_user)):
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response
    
    return templates.TemplateResponse("profile_password.html", {"request": request, "is_organizer": current_user.is_organizer})


@app.get("/profile/events")
def get_joined_events(
    request: Request,
    db_event: Session = Depends(get_event_session),
    current_user: UserBase = Depends(get_current_user)
):
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age=5)
        return response
    
    user_in_event_db = db_event.merge(current_user)
    user_events = db_event.query(EventBase).filter(EventBase.attendees.contains(user_in_event_db)).all()
    joined_event_ids = {e.uid for e in user_in_event_db.events}


    return templates.TemplateResponse("profile_events.html", {
        "request": request,
        "user_events": user_events,
        "is_organizer": current_user.is_organizer,
        'username': current_user.username if current_user else None,
        "joined_event_ids": joined_event_ids
    })


@app.get("/event/{event_id}", response_class=HTMLResponse)
def event_detail(
    request: Request,
    event_id: int,
    db_event: Session = Depends(get_event_session),
    current_user: UserBase = Depends(get_current_user)
):
    event = db_event.query(EventBase).filter(EventBase.uid == event_id).first()
    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)

    if not current_user.is_organizer:
        raise HTTPException(status_code=403, detail="Access forbidden: Not an organizer")

    event = db_event.query(EventBase).filter(EventBase.uid == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return templates.TemplateResponse("event_detail.html", {
        "request": request,
        "event": event,
        "username": current_user.username if current_user else None,
        "attendee_count": len(event.attendees),
        "is_signed_up": current_user in event.attendees if current_user else False
    })
    
@app.get("/profile/edit")
def prof_edit(request: Request, current_user: Optional[UserBase] = Depends(get_current_user)):
    
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response
    
    return templates.TemplateResponse("profile_edit.html", {"request": request, 
                                                            "first_name": current_user.first_name,
                                                            "last_name":  current_user.last_name,
                                                            "about": current_user.about,
                                                            "email":current_user.email,
                                                            "is_organizer": current_user.is_organizer,
                                                            "age": current_user.age,
                                                            "phone": current_user.phone,
                                                            "address":current_user.address
                                                            })


@app.post("/profile/edit")
def update_profile_settings(
    request: Request,
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    about: Optional[str] = Form(None),
    age: Optional[str] = Form(...),
    address: Optional[str] = Form(None),
        phone: str = Form(..., pattern=r"^\d{10,15}$"),
    
    db: Session = Depends(get_user_session),
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response

    username_conflict = db.query(UserBase).filter(
        UserBase.username == username, UserBase.uid != current_user.uid
    ).first()
    if username_conflict:
        # Optionally render the form again with an error
        return templates.TemplateResponse("profile_edit.html", {
            "request": request,
            "error": "Username already taken",
            "username": username,
            "email": email,
        }, status_code=400)
        
    if username:
        current_user.username = username

    if email:
        current_user.email = email

    if password:
        current_user.password_hashed = Hasher.get_password_hash(password)

    if about:
        current_user.about = about
        
    if age:
        current_user.age = age
    if phone:
        current_user.phone = phone
    if address:
        current_user.address = address
        
        
    if profile_picture and profile_picture.filename:
        ext = os.path.splitext(profile_picture.filename)[-1]
        new_filename = f"profile_{current_user.uid}{ext}"
        save_path = f"static/uploads/{new_filename}"
        with open(save_path, "wb") as f:
            f.write(profile_picture.file.read())
        current_user.profile_image_url = f"/static/uploads/{new_filename}"

    db.commit()
    
    if not any([username, email, password, profile_picture and profile_picture.filename]):
        response = RedirectResponse(url="/profile/edit", status_code=303)
        response.set_cookie("update_message", "No changes submitted", max_age=5)
        return response
    
    # Set success message and redirect
    response = RedirectResponse(url="/profile/home", status_code=303)
    response.set_cookie(key="update_message", value="Profile updated successfully!", max_age=5)
    return response


# -----------------------------
# Calendar
# -----------------------------

@app.get("/profile/calendar", response_class=HTMLResponse)
def prof_calendar(
    request: Request,
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age=5)
        return response

    return templates.TemplateResponse("profile_calendar.html", {
        "request": request,
        "is_organizer": current_user.is_organizer
    })

@app.get("/profile/calendar/events")
def get_user_calendar_events(
    request: Request,
    db: Session = Depends(get_event_session),
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    if current_user is None:
        return JSONResponse(status_code=403, content={"message": "Not authorized"})

    events = []
    user_in_event_db = db.merge(current_user)  # attach user to event DB session
    events = db.query(EventBase).filter(EventBase.attendees.contains(user_in_event_db)).all()

    return JSONResponse(content=events, media_type="application/json")




# @app.get("/api/user-events")
# def user_events(
#     current_user: UserBase = Depends(get_current_user),
#     db: Session = Depends(get_event_session)
# ):
#     if not current_user:
#         raise HTTPException(status_code=401, detail="Login required")
#     return db.query(EventBase).filter(EventBase.attendees.any(UserBase.uid == current_user.uid)).all()

# Testing this is commented
@app.get("/api/user-events")
def get_user_events(
    db: Session = Depends(get_event_session),
    current_user: UserBase = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not current_user:
        return []
    # Reattach current_user to the event DB session
    user_in_event_db = db.merge(current_user)

    # Query events through that relationship
    user_events = user_in_event_db.events

    events_data = [
        {
            "title": event.title,
            "start": event.start_time.isoformat(),
            "end": event.end_time.isoformat(),
            "description": event.description,
            "location": event.location,
        }
        for event in user_events
    ]
    return JSONResponse(content=events_data)


# -----------------------------
# Database Creation/Deletion
# -----------------------------

@app.get("/organizer/create_event", response_class=HTMLResponse)
def get_create_event(request: Request, current_user: Optional[UserBase] = Depends(get_current_user)):
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response

    # optionally check if user is an organizer
    if not current_user.is_organizer:
        response = RedirectResponse(url="/profile/home", status_code=302)
        response.set_cookie(
            key="not_organizer_alert",
            value="You need to be an organizer to access this page.",
            max_age=10,
            httponly=True
        )
        return response
    
    return templates.TemplateResponse("create_event.html", {"request": request, "username": current_user.username, "is_organizer": current_user.is_organizer})

@app.post("/organizer/create_event")
def post_create_event(
    request: Request,
    db: Session = Depends(get_event_session),
    organizer: Optional[UserBase] = Depends(get_current_user),
    title: str = Form(...),
    description: str = Form(None),
    event_date: str = Form(None),
    event_start_time: str = Form(None),
    event_end_time: str = Form(None),
    location: str = Form(None),
    event_type: str = Form(None),
    event_tags: str = Form(None),
    event_img_urls: str = Form(None)
):
    """
    1) Create a new event in the database
    2) Append the event info to created_events.txt
    3) Redirect to /profile/events
    """
    if organizer is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response
    
    if organizer.is_organizer == False:
        return RedirectResponse(url="/login", status_code=303)
    
    # 1) Insert event into DB
    full_organizer_name = f"{organizer.first_name} {organizer.last_name}"
    new_event = EventBase(
        owner_uid = organizer.uid,
        title=title,
        date=event_date,
        start_time = event_start_time,
        end_time = event_end_time,
        location = location,
        event_type = event_type,
        organizer = full_organizer_name,
        tags = event_tags,
        image_urls = event_img_urls,
        description=description
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # 2) Write details to text file || IDK What purpose this serves ~Kyle
    with open("created_events.txt", "a", encoding="utf-8") as f:
        f.write(f"Title: {title}\n")
        f.write(f"Description: {description}\n")
        f.write(f"Date: {event_date}\n")
        f.write("----------\n")

    return templates.TemplateResponse("create_event.html", {"request": request})


@app.get("/organizer/{organizer_id}")
def get_organizer_info(organizer_id: int, db: Session = Depends(get_user_session)):
    
    user = db.query(UserBase).filter(UserBase.uid == organizer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Organizer not found")
    return {
        "profile_image_url": user.profile_image_url,
        "name": user.username,
        "email": user.email,
        "bio": user.about,
        "age": user.age,
        "phone": user.phone,
        "address": user.address
    }

@app.get("/organizer/delete_event")
def org_del_event():
    return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
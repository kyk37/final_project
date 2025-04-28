import os
from pydantic import BaseModel
from typing import Annotated, Optional, List
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
from datetime import datetime, date, timedelta, time

from sqlalchemy import or_
from sqlalchemy import cast, Date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# from db.session import get_user_session, get_event_session
from db.session import DB_FILE, engine, sessionLocal, get_db_session

from src.usr_model import User as UserBase
from src.event_model import Events as EventBase
from src.hasher import Hasher
from src.auth import create_access_token, decode_access_token
from src.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from src.startup import create_startup_users, create_events

from calendar_router import calendar_router

from db.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Delete existing database files if they exist
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Initialize database session
    db = sessionLocal()
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

# setup calender
app.include_router(calendar_router)


async def get_token_optional(authorization: str = Header(default=None)):
    '''
        Get authorization token
    '''
    if not authorization:
        return None
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        return None
    return token

def get_current_user(request: Request, db: Session = Depends(get_db_session)):
    '''
        Get the current access token from cookie
    '''
    # get the cookie
    token = request.cookies.get("access_token")
    # print(f"[DEBUG] Token from cookies: {token}") 

    # if no cookie
    if not token:
        # print("[DEBUG] No token found in cookies")
        return None

    try:
        #  Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])#, options={"verify_exp": False}) # this option prevents verification for troubleshooting

        # print(f"[DEBUG] Decoded payload: {payload}")
        # get the user id
        user_id: str = payload.get("sub")
        
        if user_id is None:
            # print("[DEBUG] No 'sub' found in payload")
            return None
        
    except JWTError as e:
        # print(f"[DEBUG] JWT decoding error: {e}")
        return None

    # Query the userID and check if its in the database, if it is return user
    user = db.query(UserBase).filter(UserBase.uid == int(user_id)).first()
    # print(f"[DEBUG] User found: {user}")
    return user


# -----------------------------
# Home Page
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def main(
    request: Request, 
    db_event: Session = Depends(get_db_session), 
    current_user: Optional[UserBase] = Depends(get_current_user),
    page: int = 1,
    per_page: int = 20
):
    '''
        Main Home Page
    '''
    # Get the dates from today, and 7 days from now
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) 
    end_of_week = start_of_week + timedelta(days=6)        

    # return a datetime object whose components are equal to the given date objects
    start_of_week_dt = datetime.combine(start_of_week, time.min)
    end_of_week_dt = datetime.combine(end_of_week, time.max)

    events_this_week = []
    joined_event_ids = set()

    # If current user exists
    if current_user:
        print(f"Username: {current_user.username}, UID: {current_user.uid}")

        # Get all events for this week that user is part of
        events_this_week = db_event.query(EventBase).outerjoin(EventBase.attendees).filter(
            EventBase.date.between(start_of_week_dt, end_of_week_dt),
            or_(
                EventBase.owner_uid == current_user.uid,
                EventBase.attendees.contains(current_user)
                #UserBase.uid == current_user.uid
            )
        ).distinct().all()

        # print(f"Events this week for {current_user.username}: {[e.title for e in events_this_week]}")
        user_in_event_db = db_event.merge(current_user)
        joined_event_ids = {e.uid for e in user_in_event_db.events}

    # Get all the events (not just what the user is a part of)
    query = db_event.query(EventBase).filter(EventBase.archived == False)
    all_events = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Get number of attendees in all events
    attendee_counts = {event.uid: len(event.attendees) for event in all_events}
    
    # Get all titles in all events
    event_titles = {event.uid: event.title for event in all_events}
    
    # Get all event descriptions
    event_descriptions = {event.uid: event.description for event in all_events}

    # Get total number of events and separate them for each page
    total_events = query.count()
    total_pages = (total_events + per_page - 1) // per_page

    return templates.TemplateResponse('home.html', {
        'request': request,
        'username': current_user.username if current_user else None,
        'events_this_week': events_this_week,
        'all_events': all_events,
        'page': page,
        'total_pages': total_pages,
        'joined_event_ids': joined_event_ids,
        'attendee_counts': attendee_counts,
        'event_title': event_titles,
        'description': event_descriptions
    })



@app.get("/api/event/{event_id}")
def get_event_summary(
    event_id: int,
    db: Session = Depends(get_db_session),
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    '''
        Acquire events
    '''
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
    db: Session = Depends(get_db_session),
    current_user: UserBase = Depends(get_current_user)
):
    '''
        Join an event from main page
    '''
    if current_user is None:
        raise HTTPException(status_code=401, detail="User must be logged in to join events")

    # Get all events
    event = db.query(EventBase).filter(EventBase.uid == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Attach user to db session
    user_in_event_db = db.merge(current_user)

    # if user is not in the events attendee list add them and commit to database
    if user_in_event_db not in event.attendees:
        event.attendees.append(user_in_event_db)
        db.commit()
        
    else:
        raise HTTPException(status_code=400, detail="Already joined this event")

    return {"message": "Successfully joined event"}



@app.post("/api/unjoin_event/{event_id}")
def unjoin_event(
    event_id: int,
    db: Session = Depends(get_db_session),
    current_user: UserBase = Depends(get_current_user)
):
    '''
        Leave Event
    '''
    # if not logged in return
    if current_user is None:
        raise HTTPException(status_code=401, detail="User must be logged in")

    # get events
    event = db.query(EventBase).filter(EventBase.uid == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # get user db session
    user_in_event_db = db.merge(current_user)

    # if user is in the event, leave it
    if user_in_event_db in event.attendees:
        event.attendees.remove(user_in_event_db)
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="Not joined to begin with")

    return {"message": "Successfully left event"}



# -----------------------------
# Search Bar On home
# -----------------------------
@app.get("/search", response_class=HTMLResponse)
def search_events(
    request: Request,
    search: Optional[str] = "",
    db_event: Session = Depends(get_db_session),
    current_user: Optional[UserBase] = Depends(get_current_user),
    page: int = 1,
    per_page: int = 20
):
    '''
        Search function on home page
    '''
    # get the range for the week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    events_this_week = []
    joined_event_ids = set()


    if current_user:
        # get the user session
        user_in_event_db = db_event.merge(current_user)
        # get the events this week
        events_this_week = db_event.query(EventBase).filter(
            EventBase.owner_uid == current_user.uid,
            EventBase.date.between(start_of_week, end_of_week)
        ).all()
        
        # Get what events the user joined
        joined_event_ids = {e.uid for e in user_in_event_db.events}
        print(f"Events this week: {[e.title for e in events_this_week]}")
        print(f"Joined event IDs: {joined_event_ids}")

    # Query non-archived events
    base_query = db_event.query(EventBase).filter(EventBase.archived == False)

    # Search based on similar title, description, or tags
    if search:
        base_query = base_query.filter(
            EventBase.title.ilike(f"%{search}%") |
            EventBase.description.ilike(f"%{search}%") |
            EventBase.tags.ilike(f"%{search}%")
        )

    # Get basic event information and pages for display to return back to home page
    all_events = base_query.offset((page - 1) * per_page).limit(per_page).all()
    attendee_counts = {event.uid: len(event.attendees) for event in all_events}
    event_titles = {event.uid: (event.title) for event in all_events}
    total_events = base_query.count()
    total_pages = (total_events + per_page - 1) // per_page

    return templates.TemplateResponse('home.html', {
        'request': request,
        'username': current_user.username if current_user else None,
        'events_this_week': events_this_week,
        'all_events': all_events,
        'page': page,
        'total_pages': total_pages,
        'joined_event_ids': joined_event_ids,
        'attendee_counts': attendee_counts,
        'event_title': event_titles
    })
    
# -----------------------------
# LOGIN AND REGISTRATION
# -----------------------------
@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    '''
        Get the cookie if it exists, get it and send to login, and delete the cookie.
    '''
    message = request.cookies.get("message")
    response = templates.TemplateResponse("login.html", {"request": request, "message": message})
    response.delete_cookie("message")
    
    return response


@app.post("/register")
def register_user(
    new_username: str = Form(...),
    new_password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db_session)
):
    '''
        Register a new user
    '''
    # See if the username already exists
    existing_user = db.query(UserBase).filter(UserBase.username == new_username).first()
    
    # If user exists, pop flag
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash the password
    hashed_pw = Hasher.get_password_hash(new_password)

    # Setup new basic user information, and upload the hashed password to the database
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

    # create the access token using the user id, set expiration from config
    access_token = create_access_token(
        data={"sub": str(new_user.uid)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # setup a cookie to state registration is sucessful, and returns the access token
    response = JSONResponse(content={"message": "Registration successful"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,
        max_age=1800,
        samesite="lax"
    )
    return response

@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    '''
        Create the access token used for login
    '''
    # get the user
    user = db.query(UserBase).filter(UserBase.username == form_data.username).first()
    
    # if no user password check failed
    if not user or not Hasher.verify_password(form_data.password, user.password_hashed):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # make the access token
    access_token = create_access_token(
        data={"sub": str(user.uid)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # print(f"[DEBUG] Created token with expiry: {access_token}")

    response = JSONResponse(content={"access_token": access_token})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@app.post("/logout")
def logout():
    '''
        Logout
    '''
    # redirect the response back to login page
    response = RedirectResponse(url="/login", status_code=303)
    
    # Delete the access token cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False
    )
    return response

# -----------------------------
# Profile Settings
# -----------------------------
@app.get("/profile/home", response_class=HTMLResponse)
def prof_main(request: Request, current_user: Optional[UserBase] = Depends(get_current_user)):
    '''
        Profile Homepage
    '''

    # if not logged in, redirect to login page and send a cookie stating message
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 10)
        return response
    
    # if the user is not an organizer get the cookie
    cookie_msg = request.cookies.get("not_organizer_alert")

    # go to profile, home, return the cookie message to display on profile home page
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

    # if the cookie_msg exists, delete not_organizer_alert
    if cookie_msg:
        response.delete_cookie("not_organizer_alert")

    return response

# 
@app.get("/profile/security")
def prof_password(request: Request, current_user: Optional[UserBase] = Depends(get_current_user)):
    '''
        Security page
    '''
    # if user is not logged in redirect
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response
    
    # Return profile_password page, and if the user is an organizer to show the buttons on the left
    return templates.TemplateResponse("profile_password.html", {"request": request, "is_organizer": current_user.is_organizer})

# If the user changes password
@app.post("/profile/update_password")
def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db_session),
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    # Get the current user, if not logged in redirect to login
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to update your password", max_age=5)
        return response

    # Verify the current password, if the current password is wrong flag it
    if not Hasher.verify_password(current_password, current_user.password_hashed):
        return templates.TemplateResponse("profile_password.html", {
            "request": request,
            "error": "Current password is incorrect",
            "is_organizer": current_user.is_organizer
        }, status_code=400)

    # if the two new passwords are not the same.
    if new_password != confirm_password:
        return templates.TemplateResponse("profile_password.html", {
            "request": request,
            "error": "New passwords do not match",
            "is_organizer": current_user.is_organizer
        }, status_code=400)

    # get the new password if it is not the same as the current, and if the check passes
    # update db
    current_user.password_hashed = Hasher.get_password_hash(new_password)
    db.commit()

    # Send cookie saying password ahs been updated, set age of cookie
    response = RedirectResponse(url="/profile/home", status_code=303)
    response.set_cookie("update_message", "Password updated successfully", max_age=10)
    return response



@app.get("/profile/events")
def get_joined_events(
    request: Request,
    db_event: Session = Depends(get_db_session),
    current_user: UserBase = Depends(get_current_user),
    page: int = 1,
    per_page: int = 20,
    archived: bool = False
):
    # If someone attempts to access page without being logged in, return to login page
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age=10)
        return response

    # get userid
    user = db_event.query(UserBase).filter(UserBase.uid == current_user.uid).first()
    # if user id does not match return to login
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Filter user events by archived status
    if archived:
        filtered_events = [e for e in user.events if e.archived]
    else:
        filtered_events = [e for e in user.events if not e.archived]
   
   # Setup events for pages
    total_events = len(filtered_events)
    paginated = filtered_events[(page - 1) * per_page: page * per_page]
    total_pages = (total_events + per_page - 1) // per_page
    
    # get event IDS user joined
    joined_event_ids = {e.uid for e in user.events}
    
    # get number of attendees
    attendee_counts = {event.uid: len(event.attendees) for event in paginated}
    
    # Get event titles
    event_titles = {event.uid: event.title for event in paginated}
    
    # get the attendee names
    attendee_names = {
        event.uid: [f"{u.first_name} {u.last_name}" for u in event.attendees]
        for event in paginated
    }


    return templates.TemplateResponse("profile_events.html", {
        "request": request,
        "username": current_user.username,
        "user_events": paginated,
        "page": page,
        "total_pages": total_pages,
        "joined_event_ids": joined_event_ids,
        "attendee_counts": attendee_counts,
        "attendee_names": attendee_names,
        "event_title": event_titles,
        "user_id": current_user.uid,
        "is_organizer": current_user.is_organizer,
        "archived": archived
    })

    
@app.get("/profile/edit")
def prof_edit(request: Request, 
              current_user: Optional[UserBase] = Depends(get_current_user)):
    '''
        Edit the user information
    '''
    # if someone not logged in tries to access page, redirect to login
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response
    
    # return page information
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
    phone: str = Form(..., pattern=r"^\d{10,15}$"), # ensure phone number is 10-15 numbers long
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    db: Session = Depends(get_db_session),
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    # if someone not logged in attempts to access page redirect to login
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age = 5)
        return response

    # if changing username and there is a username conflict return error
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
        
    # else change rest of data if it user changed it
    if first_name:
        current_user.first_name = first_name

    if last_name:
        current_user.last_name = last_name
        
    if username:
        current_user.username = username

    if email:
        current_user.email = email

    # not on this page?
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
        
    # to change profile picture
    if profile_picture and profile_picture.filename:
        ext = os.path.splitext(profile_picture.filename)[-1]
        new_filename = f"profile_{current_user.uid}{ext}"
        save_path = f"static/uploads/{new_filename}"
        with open(save_path, "wb") as f:
            f.write(profile_picture.file.read())
        current_user.profile_image_url = f"/static/uploads/{new_filename}"

    # update the database with all the new information
    db.commit()
    
    # if no edits for username, email, password, profile pic, update no changes
    if not any([username, email, password, age, phone, address, first_name, last_name, about, profile_picture and profile_picture.filename]):
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
    # if unauthorized access redirect to login page
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age=5)
        return response

    # return calender information
    return templates.TemplateResponse("profile_calendar.html", {
        "request": request,
        "is_organizer": current_user.is_organizer
    })

@app.get("/profile/calendar/events")
def get_user_calendar_events(
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    '''
        Get calendar events the user is a part of
    '''
    # if unauthorized redirect to login
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age=5)
        return response

    events = []
    user_in_event_db = db.merge(current_user)  # attach user to event DB session
    events = db.query(EventBase).filter(EventBase.attendees.contains(user_in_event_db)).all()

    return JSONResponse(content=events, media_type="application/json")


@app.get("/api/user-events")
def get_user_events(
    db: Session = Depends(get_db_session),
    current_user: UserBase = Depends(get_current_user)
):
    ''' 
        Events in the user profile pages
    '''
    
    # if accessee is not logged in, redirect to login page
    if current_user is None:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page", max_age=5)
        return response
    
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

@app.post("/organizer/create_event", response_class=HTMLResponse)
def post_create_event(
    request: Request,
    db: Session = Depends(get_db_session),
    organizer: Optional[UserBase] = Depends(get_current_user),
    title: str = Form(...),
    description: str = Form(None),
    event_date: str = Form(...), 
    event_start_time: str = Form(...),
    event_end_time: str = Form(...),
    location: str = Form(...),
    event_type: str = Form(...),
    event_tags: str = Form(None),
    event_img_urls: Optional[List[UploadFile]] = File(None),
):
    ''' 
        Create Events! 
    '''
    # if the user attempts to access create_event and is not an organizer, return to login state only event organizers can access this page
    if organizer is None or not organizer.is_organizer:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Only event organizers can access this page", max_age=5)
        return response

    try:
        # Parse the dates and times given from user
        parsed_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        parsed_start_time = datetime.strptime(event_start_time, "%H:%M").time()
        parsed_end_time = datetime.strptime(event_end_time, "%H:%M").time()
        start_dt = datetime.combine(parsed_date, parsed_start_time)
        end_dt = datetime.combine(parsed_date, parsed_end_time)

        # Verify event is in the future, if its not, archive it
        is_archived = end_dt < datetime.now()
        
        # Get organizer name
        full_organizer_name = f"{organizer.first_name} {organizer.last_name}"

        # So the user can upload images
        image_paths = []
        if event_img_urls:
            os.makedirs("static/uploads", exist_ok=True)
            for img in event_img_urls:
                if img and img.filename:
                    ext = os.path.splitext(img.filename)[-1]
                    filename = f"event_{organizer.uid}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{img.filename}"
                    save_path = f"static/uploads/{filename}"
                    with open(save_path, "wb") as f:
                        f.write(img.file.read())
                    image_paths.append(f"/static/uploads/{filename}")

        # Create the new event and add it to the database
        new_event = EventBase(
            owner_uid=organizer.uid,
            title=title,
            date=parsed_date,
            start_time=start_dt,
            end_time=end_dt,
            location=location,
            event_type=event_type,
            organizer=full_organizer_name,
            tags=event_tags,
            image_urls=",".join(image_paths),
            description=description,
            archived=is_archived
        )
        # add the user/organizer to the session
        organizer_in_db = db.merge(organizer)
        # Set the organizer as an attendee
        new_event.attendees.append(organizer_in_db)

        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        return templates.TemplateResponse("create_event.html", {
            "request": request,
            "success": True,
            "event": new_event
        })

    except ValueError:
        return templates.TemplateResponse("create_event.html", {
            "request": request,
            "error": "Invalid datetime format. Please use YYYY-MM-DDTHH:MM (datetime-local)."
        })

    except Exception as e:
        print(f"[ERROR] Failed to create event: {e}")
        return templates.TemplateResponse("create_event.html", {
            "request": request,
            "error": "An unexpected error occurred while creating the event."
        })


@app.get("/organizer/create_event", response_class=HTMLResponse)
def get_create_event(
    request: Request,
    current_user: Optional[UserBase] = Depends(get_current_user)
):
    # if the user accessing the create_event page is not an organizer send to login, flag
    if current_user is None or not current_user.is_organizer:
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie("message", "Please log in as an organizer", max_age=5)
        return response

    return templates.TemplateResponse("create_event.html", {
        "request": request,
        "is_organizer": current_user.is_organizer
    })

@app.put("/api/edit_event/{event_id}")
def edit_event(event_id: int, data: dict, db: Session = Depends(get_db_session), current_user: UserBase = Depends(get_current_user)):
    
    # edit the event information, get the event
    event = db.get(EventBase, event_id)

    # if event is not found flag
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # if someone who is not the organizer who created it, flag
    if event.owner_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="You are not authorized to edit this event")

    # Verify the owner is in the list of attendees, and add them if they are not (just in case)
    if event.owner_uid and event.owner_uid not in [u.uid for u in event.attendees]:
        organizer = db.query(UserBase).filter(UserBase.uid == event.owner_uid).first()
        if organizer:
            event.attendees.append(organizer)

    # Get all the information from the event, so it can be placed into the text boxes. So user knows what's being modified
    event.title = data.get("title", event.title)
    event.location = data.get("location", event.location)
    event.tags = data.get("tags", event.tags)
    event.description = data.get("description", event.description)
    event.event_type = data.get("event_type", event.event_type)
    event.image_urls = data.get("image_urls", event.image_urls)

    # Check the format of start/end time if invalid flag
    try:
        if data.get("start_time"):
            event.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            event.end_time = datetime.fromisoformat(data["end_time"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Please use ISO 8601 format.")

    # update database
    db.commit()
    return {"message": "Event updated successfully"}
    
    
    

@app.delete("/api/delete_event/{event_id}")
def delete_event(event_id: int, 
                 db: Session = Depends(get_db_session), 
                current_user: Optional[UserBase] = Depends(get_current_user)):
    '''
        Delete the event
    '''
    # Check if the event exists, if it doesn't flag, else delete
    event = db.query(EventBase).filter(EventBase.uid == event_id, EventBase.owner_uid == current_user.uid).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or unauthorized")
    db.delete(event)
    db.commit()
    return {"message": "Event deleted"}




@app.get("/organizer/{organizer_id}")
def get_organizer_info(organizer_id: int, db: Session = Depends(get_db_session)):
    '''
        if the organizer is not found flag
    '''
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
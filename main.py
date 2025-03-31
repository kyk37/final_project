from pydantic import BaseModel
from typing import Annotated
from fastapi import FastAPI, Form, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

#database setup
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#user model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    #TODO: Hash passwords?

#db tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse('home.html', {'request':request} )

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
    
@app.get("/profile/settings")
def prof_settings(request: Request):
    return templates.TemplateResponse("profile_settings.html", {"request": request})

@app.post("/profile/settings")
def update_profile_settings(
    username: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    db: SessionLocal = Depends(get_db)
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

@app.get("/profile/home")
def prof_main():
    return

@app.get("/profile/security")
def prof_password():
    return

@app.get("/profile/events")
def prof_events():
    return

@app.get("/profile/calendar")
def prof_calendar():
    return

@app.get("/organizer/create_event")
def org_create_event():
    return

@app.get("/organizer/delete_event")
def org_del_event():
    return


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
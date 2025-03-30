from pydantic import BaseModel
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse('home.html', {'request':request} )


@app.get("/login")
def login():
    return


@app.get("/profile/home")
def prof_main():
    return

@app.get("/profile/settings")
def prof_settings():
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
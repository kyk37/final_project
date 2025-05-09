USERS: (username:password)
- test:test
- admin:admin
- cs_department:organizer
- student_council:organizer
- wellness_club:organizer
- career_center:organizer
- ai_lab:organizer

# Event Management System 
To import anaconda environment see environment.yaml

# Library/Module Requirements
- FastAPI: pip install fastapi[all]: https://fastapi.tiangolo.com/
- pip install fastapi-users[all] (for sqlachemy w/ fastapi)
- Google Calender: https://developers.google.com/calendar/api/v3/reference/events#methods
- SQLAlchemy (Database): https://www.sqlalchemy.org/
- PyJWT: (Password Hashing)
- passlib
- bcrypt
- openssl
- JWT: pip install python-jose[cryptography]

---> https?

## -- Basic Requirements --
- [X] Landing Page (with list of events, and event title, time, location, type)
- [X] Search function to find events using tags/keywords
- [X] Users can view each event's details, title, type, tags, organizer, time, location, preview images, and description.
- [X] Registration/login portal.
- [X] Registered users can sign up for future events, and view number of registeres users signed up
- [X] user profile page/settings. Show events with preview
- [X] Event Manager accounts (tied to specific event organizers) Can publish, edit, cancel events ~see item 6
- [X] Event manager profile page shows events they are managing. Can also view the detail page, edit event information, cancel event, and see a list of registered users that joined the event
- [X] All past events should be archived, no changes and no signups are allowed to past events

## -- Tech Reqs --
- [X] User friendly web interface ~ish
- [X] should support many users (We have like 8? could generate more)
- [X] persistent storage (Do not store in plain text) (Hash/encryption) Mysql?
- [ ] 75% code coverage for unit tests (idk what this means ~Kyle)


## -- Advanced Requirements
- [X] Uses a database (we use two)
- [X] multiple platform support (web, phone, CLI)
- [ ] restful API for all functionalities with clear documents
- [ ] event detail provides map information (Map apis), can download calendar event
- [ ] allows registered users to subscribe to certain tags and organizers
- [ ] event manager account allows batch creation from CSV imports and batch event cancelling
- [ ] system to provide a filter function on all event lists using event type, time, location etc.

#### Writen By:
- Kyle Kessler
- Dan Hiss
- Danny Wan

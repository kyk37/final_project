# Event Management System 
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
- [ ] Landing Page (with list of events, and event title,time, location, type
- [ ] Search function to find events using tags/keywords
- [ ] Users can view eachother's details
- [ ] Registration/login portal.
- [ ] Registered users can sign up for future events, and view number of registeres users signed up
- [ ] user profile page/settings. Show events with preview
- [ ] Event Manager accounts (tied to specific event organizers) Can publish, edit, cancel events ~see item 6
- [ ] Event manager profile page shows events they are managing ~ see reqs for 7
- [ ] All past events should be archived, no changes, and signups are allowed to past events


## -- Tech Reqs --
- [ ] User friendly web interface
- [ ] should support many users
- [ ] persistent storage (Do not store in plain text) (Hash/encryption) Mysql?
- [ ] 75% code coverage for unit tests


## -- Advanced Requirements
- [ ] Uses a database
- [ ] multiple platform support (web, phone, CLI)
- [ ] restful API for all functionalities with clear documents
- [ ] event detail provides map information (Map apis), can download calendar event
- [ ] allows registered users to subscribe to certain tags and organizers
- [ ] event manager account allows batch creation from CSV imports and batch event cancelling
- [ ] system to provide a filter function on all event lists using event type, time, locationetc.

#### Writen By:
- Kyle Kessler
- Dan Hiss

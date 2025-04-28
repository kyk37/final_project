from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from src.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: timedelta = None):
    '''
        Create the Acccess token
    '''
    # Copy the data to encode
    to_encode = data.copy()
    # Set the expiration to 120 minutes
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # print(f"[DEBUG] Token will expire at (UTC): {expire}")
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    # print(f"[DEBUG] Server current UTC time: {datetime.now(timezone.utc)}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
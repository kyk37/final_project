from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from src.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, ISSUER, ALLOWED_AUDIENCES
from fastapi import HTTPException
from jose.exceptions import ExpiredSignatureError

def create_access_token(data: dict, audience:str, expires_delta: timedelta = None):
    '''
        Create the Acccess token
    '''
    # Copy the data to encode
    to_encode = data.copy()
    
    # Set the expiration to 120 minutes
    now = datetime.now(timezone.utc) 
    
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    print(f"[DEBUG] Token will expire at (UTC): {expire}")
    
    
    to_encode.update({"exp": expire,
                      "iat": now,
                      "iss": ISSUER,
                      "aud": audience})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    # for every option in allowed audiences
    for aud in ALLOWED_AUDIENCES:
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                audience=aud,
                issuer=ISSUER
            )
            # get iat and user_id
            user_id: str = payload.get("sub")
            iat: int = payload.get("iat")

            if user_id is None or iat is None:
                raise HTTPException(status_code=403, detail="Invalid token content")

            return {
                "user_id": user_id,
                "issued_at": datetime.fromtimestamp(iat, tz=timezone.utc),  
                "issuer": payload.get("iss"),
                "audience": payload.get("aud")
            }

        except ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token has expired")
        except JWTError as e:
            print(f"[DEBUG] Failed for audience '{aud}': {e}")
            continue  # Try next audience

    raise HTTPException(status_code=403, detail="Token audience invalid")

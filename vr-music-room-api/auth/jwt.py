import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

SECRET = os.getenv("JWT_SECRET", "fallback-secret")
ALGORITHM = "HS256"
EXPIRE_HOURS = 24

security = HTTPBearer()

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency — extracts user_id from the JWT token."""
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
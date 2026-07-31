import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from app.core.security import verify_password, create_access_token

load_dotenv()  
router = APIRouter(prefix="/auth", tags=["auth"])
TEAM_USERNAME = os.getenv("TEAM_USERNAME")
TEAM_PASSWORD_HASH = os.getenv("TEAM_PASSWORD_HASH")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != TEAM_USERNAME or not verify_password(
        form_data.password, TEAM_PASSWORD_HASH
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}
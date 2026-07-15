from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=2, max_length=255)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

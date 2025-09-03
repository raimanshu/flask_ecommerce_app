import uuid
import bcrypt
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time, string_to_base64
from management.entities.entity_base.schema import DefaultEntityBase

class UserBase(DefaultEntityBase):
    user_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the user",
    )
    username: str = Field(
        min_length=3,
        default=None,
        strip_whitespace=True,
        description="Username of the user",
    )
    name: str = Field(
        min_length=3,
        default=None,
        strip_whitespace=True,
        description="Full name of the user",
    )
    email: EmailStr = Field(
        strip_whitespace=True,
        description="Email address of the user",
    )
    password:str = Field(
        min_length=6,
        # max_length=15,
        default=None,
        strip_whitespace=True,
        description="Password for the user account",
    )
    contact_number: str = Field(
        default=None,
        strip_whitespace=True,
        description="Contact number of the user",
    )
    # address: str = Field(
    #     default=None,
    #     strip_whitespace=True,
    #     description="Address of the user",
    # )
    is_active: bool = Field(
        default=True,
        strip_whitespace=True,
        description="Indicates if the user account is active",
    ) 

class AdditionalValidators:
    # @validator("username")
    # def validate_username(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("Username must be at least 3 characters long.")
    #     return value

    # @root_validator(pre=True)
    # def validate_password(cls, values):
    #     password = values.get("password")
    #     if not password or len(password) < 6:
    #         raise ValueError("Password must be at least 6 characters long.")
    #     if not password or len(password) > 15:
    #         raise ValueError("Password must not exceed 15 characters.")
    #     if password:
    #         values["password"] = password
    #     return values

    @root_validator(pre=True)
    @classmethod
    def set_password(cls, values):
        password = values.get("password")
        if password:
            values["password"] = string_to_base64(password)
            # values["password"] = bcrypt.hashpw(password, bcrypt.gensalt())
        return values
    
class UserCreate(AdditionalValidators, UserBase):

    @validator("user_id", pre=True, always=True)
    @classmethod
    def generate_user_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v
    
class UserUpdate(AdditionalValidators, UserBase):
    name:Optional[str] = None
    email:Optional[EmailStr] = None
    password:Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values

class UserDelete(UserBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

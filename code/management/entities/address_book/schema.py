import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase

class AddressBookBase(DefaultEntityBase):
    address_book_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the address_book",
    )
    address_bookname: str = Field(
        min_length=3,
        default=None,
        strip_whitespace=True,
        description="AddressBookname of the address_book",
    )
    name: str = Field(
        min_length=3,
        default=None,
        strip_whitespace=True,
        description="Full name of the address_book",
    )
    email: EmailStr = Field(
        strip_whitespace=True,
        description="Email address of the address_book",
    )
    password:str = Field(
        min_length=6,
        max_length=15,
        default=None,
        strip_whitespace=True,
        description="Password for the address_book account",
    )
    contact_number: str = Field(
        default=None,
        strip_whitespace=True,
        description="Contact number of the address_book",
    )
    address: str = Field(
        default=None,
        strip_whitespace=True,
        description="Address of the address_book",
    )
    is_active: bool = Field(
        default=True,
        strip_whitespace=True,
        description="Indicates if the address_book account is active",
    ) 

class AdditionalValidators:
    # @validator("address_bookname")
    # def validate_address_bookname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("AddressBookname must be at least 3 characters long.")
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
            values["password"] = password
        return values
    
class AddressBookCreate(AdditionalValidators, AddressBookBase):

    @validator("address_book_id", pre=True, always=True)
    @classmethod
    def generate_address_book_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v
    
class AddressBookUpdate(AdditionalValidators, AddressBookBase):
    name:Optional[str] = None
    email:Optional[EmailStr] = None
    password:Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values

class AddressBookDelete(AddressBookBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

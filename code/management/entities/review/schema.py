import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class ReviewBase(DefaultEntityBase):
    review_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the review",
    )
    user_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the user",
    )
    product_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the product",
    )
    rating: int = Field(
        default=0,
        strip_whitespace=True,
        description="Rating of the review",
    )
    comment: str = Field(
        default=None,
        strip_whitespace=True,
        description="Comment of the review",
    )


class AdditionalValidators:
    # @validator("reviewname")
    # def validate_reviewname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("Reviewname must be at least 3 characters long.")
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


class ReviewCreate(AdditionalValidators, ReviewBase):

    @validator("review_id", pre=True, always=True)
    @classmethod
    def generate_review_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class ReviewUpdate(AdditionalValidators, ReviewBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class ReviewDelete(ReviewBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase

class ProductImageBase(DefaultEntityBase):
    product_image_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the product_image",
    )
    product_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Unique identifier for the product",
    )
    image_url: str = Field(
        default=None,
        strip_whitespace=True,
        description="Image url of the product",
    )
    alt_text: str = Field(
        default=None,
        strip_whitespace=True,
        description="Alt text of the product",
    )
    is_main: bool = Field(
        default=False,
        strip_whitespace=True,
        description="Is main image of the product",
    )

class AdditionalValidators:
    # @validator("product_imagename")
    # def validate_product_imagename(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("ProductImagename must be at least 3 characters long.")
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
    
class ProductImageCreate(AdditionalValidators, ProductImageBase):

    @validator("product_image_id", pre=True, always=True)
    @classmethod
    def generate_product_image_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v
    
class ProductImageUpdate(AdditionalValidators, ProductImageBase):
    name:Optional[str] = None
    email:Optional[EmailStr] = None
    password:Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values

class ProductImageDelete(ProductImageBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

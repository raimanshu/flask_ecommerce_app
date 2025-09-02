import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class ProductBase(DefaultEntityBase):
    product_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the product",
    )
    name: str = Field(
        min_length=3,
        default=None,
        strip_whitespace=True,
        description="Full name of the product",
    )
    slug: str = Field(
        min_length=3,
        default=None,
        strip_whitespace=True,
        description="Slug of the product",
    )
    description: str = Field(
        min_length=3,
        default=None,
        strip_whitespace=True,
        description="Description of the product",
    )
    brand_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Unique identifier for the brand",
    )
    category_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Unique identifier for the category",
    )
    price: float = Field(
        default=None,
        strip_whitespace=True,
        description="Price of the product",
    )
    discount_price: float = Field(
        default=None,
        strip_whitespace=True,
        description="Discount price of the product",
    )
    sku: str = Field(
        default=None,
        strip_whitespace=True,
        description="Sku of the product",
    )
    is_active: bool = Field(
        default=True,
        strip_whitespace=True,
        description="Is active of the product",
    )


class AdditionalValidators:
    # @validator("productname")
    # def validate_productname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("Productname must be at least 3 characters long.")
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


class ProductCreate(AdditionalValidators, ProductBase):

    @validator("product_id", pre=True, always=True)
    @classmethod
    def generate_product_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class ProductUpdate(AdditionalValidators, ProductBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class ProductDelete(ProductBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class CartItemBase(DefaultEntityBase):
    cart_item_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the cart_item",
    )
    cart_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the cart",
    )
    product_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the product",
    )
    quantity: int = Field(
        default=1,
        strip_whitespace=True,
        description="Quantity of the product in the cart",
    )
    added_at: str = Field(
        default=get_current_time(),
        strip_whitespace=True,
        description="Date and time when the product was added to the cart",
    )


class AdditionalValidators:
    # @validator("cart_itemname")
    # def validate_cart_itemname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("CartItemname must be at least 3 characters long.")
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


class CartItemCreate(AdditionalValidators, CartItemBase):

    @validator("cart_item_id", pre=True, always=True)
    @classmethod
    def generate_cart_item_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class CartItemUpdate(AdditionalValidators, CartItemBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class CartItemDelete(CartItemBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

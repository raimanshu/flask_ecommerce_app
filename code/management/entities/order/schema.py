import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class OrderBase(DefaultEntityBase):
    order_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the order",
    )
    user_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Unique identifier for the user",
    )
    order_number: str = Field(
        default=None,
        strip_whitespace=True,
        description="Order number",
    )
    total_amount: float = Field(
        default=0.0,
        strip_whitespace=True,
        description="Total amount of the order",
    )
    shipping_fee: float = Field(
        default=0.0,
        strip_whitespace=True,
        description="Shipping fee of the order",
    )
    discount_amount: float = Field(
        default=0.0,
        strip_whitespace=True,
        description="Discount amount of the order",
    )
    payment_status: str = Field(
        default=None,
        strip_whitespace=True,
        description="Payment status of the order",
    )
    order_status: str = Field(
        default=None,
        strip_whitespace=True,
        description="Order status of the order",
    )
    shipping_address_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Shipping address id of the order",
    )
    billing_address_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Billing address id of the order",
    )


class AdditionalValidators:
    # @validator("ordername")
    # def validate_ordername(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("Ordername must be at least 3 characters long.")
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


class OrderCreate(AdditionalValidators, OrderBase):

    @validator("order_id", pre=True, always=True)
    @classmethod
    def generate_order_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class OrderUpdate(AdditionalValidators, OrderBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class OrderDelete(OrderBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class ShippingBase(DefaultEntityBase):
    shipping_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the shipping",
    )
    order_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the order",
    )
    courier_name: str = Field(
        default=None,
        strip_whitespace=True,
        description="Courier name for the shipping",
    )
    tracking_number: str = Field(
        default=None,
        strip_whitespace=True,
        description="Tracking number for the shipping",
    )
    shipped_at: str = Field(
        default=get_current_time(),
        strip_whitespace=True,
        description="Shipped at for the shipping",
    )
    delivered_at: str = Field(
        default=None,
        strip_whitespace=True,
        description="Delivered at for the shipping",
    )


class AdditionalValidators:
    # @validator("shippingname")
    # def validate_shippingname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("Shippingname must be at least 3 characters long.")
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


class ShippingCreate(AdditionalValidators, ShippingBase):

    @validator("shipping_id", pre=True, always=True)
    @classmethod
    def generate_shipping_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class ShippingUpdate(AdditionalValidators, ShippingBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class ShippingDelete(ShippingBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

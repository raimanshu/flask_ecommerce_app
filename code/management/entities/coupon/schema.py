import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class CouponBase(DefaultEntityBase):
    coupon_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the coupon",
    )
    code: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the coupon",
    )
    discount_value: float = Field(
        default=0.0,
        strip_whitespace=True,
        description="Discount value for the coupon",
    )
    min_order_value: float = Field(
        default=0.0,
        strip_whitespace=True,
        description="Minimum order value for the coupon",
    )
    max_discount: float = Field(
        default=0.0,
        strip_whitespace=True,
        description="Maximum discount for the coupon",
    )
    valid_from: str = Field(
        default=get_current_time(),
        strip_whitespace=True,
        description="Valid from date for the coupon",
    )
    valid_to: str = Field(
        default=get_current_time(),
        strip_whitespace=True,
        description="Valid to date for the coupon",
    )
    is_active: bool = Field(
        default=True,
        strip_whitespace=True,
        description="Indicates if the coupon is active or not",
    )
    usage_limit: int = Field(
        default=0,
        strip_whitespace=True,
        description="Usage limit for the coupon",
    )
    usage_count: int = Field(
        default=0,
        strip_whitespace=True,
        description="Usage count for the coupon",
    )


class AdditionalValidators:
    # @validator("couponname")
    # def validate_couponname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("Couponname must be at least 3 characters long.")
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


class CouponCreate(AdditionalValidators, CouponBase):

    @validator("coupon_id", pre=True, always=True)
    @classmethod
    def generate_coupon_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class CouponUpdate(AdditionalValidators, CouponBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class CouponDelete(CouponBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase

class PaymentBase(DefaultEntityBase):
    payment_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the payment",
    )
    order_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the order",
    )
    payment_method: str = Field(
        default=None,
        strip_whitespace=True,
        description="Payment method for the payment",
    )
    payment_reference: str = Field(
        default=None,
        strip_whitespace=True,
        description="Payment reference for the payment",
    )
    amount: float = Field(
        default=None,
        strip_whitespace=True,
        description="Amount for the payment",
    )
    status: str = Field(
        default=None,
        strip_whitespace=True,
        description="Status for the payment",
    )
    paid_at: str = Field(
        default=get_current_time(),
        strip_whitespace=True,
        description="Paid at for the payment",
    )

class AdditionalValidators:
    # @validator("paymentname")
    # def validate_paymentname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("Paymentname must be at least 3 characters long.")
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
    
class PaymentCreate(AdditionalValidators, PaymentBase):

    @validator("payment_id", pre=True, always=True)
    @classmethod
    def generate_payment_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v
    
class PaymentUpdate(AdditionalValidators, PaymentBase):
    name:Optional[str] = None
    email:Optional[EmailStr] = None
    password:Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values

class PaymentDelete(PaymentBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

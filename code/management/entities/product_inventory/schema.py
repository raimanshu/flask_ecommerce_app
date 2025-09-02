import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class ProductInventoryBase(DefaultEntityBase):
    product_inventory_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the product_inventory",
    )
    product_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Unique identifier for the product",
    )
    stock_quantity: int = Field(
        default=0,
        strip_whitespace=True,
        description="Stock quantity of the product",
    )
    reserved_quantity: int = Field(
        default=0,
        strip_whitespace=True,
        description="Reserved quantity of the product",
    )
    warehouse_location: str = Field(
        default=None,
        strip_whitespace=True,
        description="Warehouse location of the product",
    )


class AdditionalValidators:
    # @validator("product_inventoryname")
    # def validate_product_inventoryname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("ProductInventoryname must be at least 3 characters long.")
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


class ProductInventoryCreate(AdditionalValidators, ProductInventoryBase):

    @validator("product_inventory_id", pre=True, always=True)
    @classmethod
    def generate_product_inventory_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class ProductInventoryUpdate(AdditionalValidators, ProductInventoryBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class ProductInventoryDelete(
    ProductInventoryBase
):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

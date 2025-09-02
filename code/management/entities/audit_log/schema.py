import uuid
from typing import Optional
from pydantic import EmailStr, Field, root_validator, validator

from utils.utility import get_current_time
from management.entities.entity_base.schema import DefaultEntityBase


class AuditLogBase(DefaultEntityBase):
    audit_log_id: str = Field(
        default=str(uuid.uuid4()),
        strip_whitespace=True,
        description="Unique identifier for the audit_log",
    )
    entity_type: str = Field(
        default=None,
        strip_whitespace=True,
        description="Type of the entity",
    )
    entity_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Unique identifier for the entity",
    )
    action: str = Field(
        default=None,
        strip_whitespace=True,
        description="Action performed on the entity",
    )
    user_id: str = Field(
        default=None,
        strip_whitespace=True,
        description="Unique identifier for the user",
    )
    old_data: str = Field(
        default=None,
        strip_whitespace=True,
        description="Old data of the entity",
    )
    new_data: str = Field(
        default=None,
        strip_whitespace=True,
        description="New data of the entity",
    )


class AdditionalValidators:
    # @validator("audit_logname")
    # def validate_audit_logname(cls, value):
    #     if not value or len(value) < 3:
    #         raise ValueError("AuditLogname must be at least 3 characters long.")
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


class AuditLogCreate(AdditionalValidators, AuditLogBase):

    @validator("audit_log_id", pre=True, always=True)
    @classmethod
    def generate_audit_log_id(cls, v):
        if v:
            return str(uuid.uuid4())
        return v


class AuditLogUpdate(AdditionalValidators, AuditLogBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_modified_at(cls, values):
        values["modified_at"] = get_current_time()
        return values


class AuditLogDelete(AuditLogBase):  # pylint: disable=too-few-public-methods
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @root_validator(pre=True)
    @classmethod
    def set_deleted_at(cls, values):
        values["deleted_at"] = get_current_time()
        return values

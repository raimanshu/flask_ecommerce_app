from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, typing, validator


class DefaultEntityBase(BaseModel):

    attributes: dict[str, typing.Any] = Field(
        default={}, description="Stores the other attributes of the entity"
    )
    created_by: Optional[str] = Field(
        default=None,
        strip_whitespace=True,
        description="Unique Identifier of user who created the entity.",
    )
    created_at: datetime = Field(
        default=datetime.now(timezone.utc).replace(tzinfo=None),
        description="Creation date and time of the entity data.",
        validators=["is_datetime"],
    )
    modified_by: Optional[str] = Field(
        default=None,
        strip_whitespace=True,
        description="Unique Identifier of user who updated the entity.",
    )
    modified_at: Optional[datetime] = Field(
        default=None,
        description="Updation date and time of the entity data.",
        validators=["is_datetime"],
    )
    deleted_by: Optional[str] = Field(
        default=None,
        strip_whitespace=True,
        description="Unique Identifier of user who deleted the entity.",
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Deleted date and time of the entity data.",
        validators=["is_datetime"],
    )

    @validator("attributes", pre=True)
    @classmethod
    def ensure_dict(cls, v: typing.Any):
        if not isinstance(v, dict):
            raise ValueError("attributes must be a dictionary")
        return v

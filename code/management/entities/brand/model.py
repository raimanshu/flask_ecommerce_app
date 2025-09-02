from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Brand(db.Model):
    __tablename__ = "brand"

    brand_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    name = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    attributes = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    modified_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    modified_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)

    products = db.relationship('Product', backref='brand')

    def to_dict(self):
        return {
            "brand_id": self.brand_id,
            "name": self.name,
            "description": self.description,
            "attributes": self.attributes,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "modified_at": self.modified_at if self.modified_at else None,
            "modified_by": self.modified_by,
            "deleted_at": self.deleted_at if self.deleted_at else None,
            "deleted_by": self.deleted_by,
        }

    def add(self):
        try:
            logger.debug(f"Adding brand: {self} to brand table")
            return _add_brand(self)
        except Exception as e:
            logger.exception(f"Error adding brand: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating brand: {self} to brand table")
            return _update_brand(self)
        except Exception as e:
            logger.exception(f"Error updating brand: {e}")
            return False, None

    def delete(brand):
        try:
            logger.debug(f"Deleting brand: {brand} from brand table")
            return _delete_brand(brand)
        except Exception as e:
            logger.exception(f"Error deleting brand: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching brand: {content} from brand table")
            return _get_brand(content)
        except Exception as ex:
            logger.exception(f"Error fetching brand: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all brands from brand table")
            return _get_all_brands(content)
        except Exception as ex:
            logger.exception(f"Error fetching all brands: {ex}")
            return False, None


class BrandProvider(Brand):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching brand by attribute {attribute_name}: {content}")
            return _get_brand_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in BrandProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_brand_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in BrandProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Brand Helper Functions


def _get_brand(content):
    try:
        logger.debug(f"Fetching brand: {content}")
        if content.get("brand", ""):
            content["brand_id"] = content["brand"].brand_id
        elif content.get("entity_id", ""):
            content["brand_id"] = content["entity_id"]
        brand = None
        # brand = Brand.query.filter_by(brand_id=content["brand_id"]).first()
        brand_query = db.session.query(Brand).filter_by(brand_id=content["brand_id"])
        if not content.get("include_deleted"):
            brand_query = brand_query.filter(Brand.deleted_by.is_(None))
        brand = brand_query.first()
        if not brand:
            logger.debug("Brand not found")
            return False, None
        brand_dict = brand.to_dict()
        logger.success(f"Brand fetched: {brand_dict}")
        return True, brand_dict
    except Exception as ex:
        logger.exception(f"Error fetching brand: {ex}")
        raise ex


def _get_all_brands(content):
    try:
        logger.debug(f"Fetching all brands: {content}")
        brand = None
        # brand = Brand.query.all()
        brand_query = db.session.query(Brand)
        if not content.get("include_deleted"):
            brand_query = brand_query.filter(Brand.deleted_by.is_(None))
        brand = brand_query.all()
        if not brand:
            logger.debug("No brands found")
            return False, None
        logger.success(f"Brands fetched: {brand}")
        return True, brand
    except Exception as ex:
        logger.exception(f"Error fetching all brands: {ex}")
        raise ex


def _delete_brand(brand):
    try:
        logger.debug(f"Deleting brand: {brand}")
        # Brand.query.filter_by(brand_id=brand.brand_id).delete()
        db.session.query(Brand).filter_by(brand_id=brand.brand_id).delete()
        db.session.commit()
        logger.success(f"Brand deleted: {brand}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting brand: {ex}")
        db.session.rollback()
        return ex


def _add_brand(brand):
    try:
        logger.debug(f"Adding brand: {brand}")
        db.session.add(brand)
        db.session.commit()
        db.session.refresh(brand)
        brand_dict = brand.to_dict()
        logger.success(f"Brand added: {brand_dict}")
        return True, brand
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding brand: {ex}")
        db.session.rollback()
        raise ex


def _update_brand(brand):
    try:
        logger.debug(f"Updating brand: {brand}")
        updated_brand = None
        # Brand.query.filter_by(brand_id=brand.brand_id).update(brand.to_dict())
        updated_brand = db.session.merge(brand)
        db.session.commit()
        if not updated_brand:
            logger.exception("Brand not updated")
            return False, None
        updated_brand_dict = updated_brand.to_dict()
        logger.success(f"Brand updated: {updated_brand_dict}")
        return True, updated_brand_dict
    except Exception as ex:
        logger.exception(f"Error updating brand: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region BrandProvider Helper Functions
def _get_brand_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching brand by attribute {attribute_name}: {content}")
        brand = None
        brand_query = db.session.query(Brand).filter(
            getattr(Brand, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            brand_query = brand_query.filter(Brand.deleted_by.is_(None))
        brand = brand_query.first()
        if not brand:
            logger.debug(
                f"No brand found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        brand_dict = brand.to_dict()
        logger.success(f"Brand fetched by attribute {attribute_name}: {brand_dict}")
        return True, brand
    except Exception as ex:
        logger.exception(f"Error fetching brand by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_brand_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective brand data by attribute {attribute_name}: {content}"
        )
        brands_dict = None
        brands = (
            db.session.query(Brand)
            .filter(
                getattr(Brand, attribute_name).in_(content.get(f"{attribute_name}", []))
            )
            .all()
        )
        if require_object:
            brands_dict = {
                getattr(brand_data, attribute_name): brand_data for brand_data in brands
            }
        else:
            brands_dict = {
                getattr(brand_data, attribute_name): brand_data.to_dict()
                for brand_data in brands
            }
        if not brands_dict:
            logger.debug(
                f"No brands found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(f"Brands fetched by attribute {attribute_name}: {brands_dict}")
        return True, brands_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective brand data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from infra.logging import logger
from sqlalchemy import Table, Column, Integer, ForeignKey


class Category(db.Model):
    __tablename__ = "category"

    category_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    name = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    slug = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False, unique=True)
    parent_category_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("category.category_id"), nullable=True)
    # parent_category_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
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

    parent = relationship("Category", remote_side=[category_id], backref="children")
    products = db.relationship('Product', backref='category')

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "name": self.name,
            "slug": self.slug,
            "parent_id": self.parent_id,
            "contact_number": self.contact_number,
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
            logger.debug(f"Adding category: {self} to category table")
            return _add_category(self)
        except Exception as e:
            logger.exception(f"Error adding category: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating category: {self} to category table")
            return _update_category(self)
        except Exception as e:
            logger.exception(f"Error updating category: {e}")
            return False, None

    def delete(category):
        try:
            logger.debug(f"Deleting category: {category} from category table")
            return _delete_category(category)
        except Exception as e:
            logger.exception(f"Error deleting category: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching category: {content} from category table")
            return _get_category(content)
        except Exception as ex:
            logger.exception(f"Error fetching category: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all categorys from category table")
            return _get_all_categorys(content)
        except Exception as ex:
            logger.exception(f"Error fetching all categorys: {ex}")
            return False, None


class CategoryProvider(Category):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching category by attribute {attribute_name}: {content}")
            return _get_category_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in CategoryProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_category_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in CategoryProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Category Helper Functions


def _get_category(content):
    try:
        logger.debug(f"Fetching category: {content}")
        if content.get("category", ""):
            content["category_id"] = content["category"].category_id
        elif content.get("entity_id", ""):
            content["category_id"] = content["entity_id"]
        category = None
        # category = Category.query.filter_by(category_id=content["category_id"]).first()
        category_query = db.session.query(Category).filter_by(
            category_id=content["category_id"]
        )
        if not content.get("include_deleted"):
            category_query = category_query.filter(Category.deleted_by.is_(None))
        category = category_query.first()
        if not category:
            logger.debug("Category not found")
            return False, None
        category_dict = category.to_dict()
        logger.success(f"Category fetched: {category_dict}")
        return True, category_dict
    except Exception as ex:
        logger.exception(f"Error fetching category: {ex}")
        raise ex


def _get_all_categorys(content):
    try:
        logger.debug(f"Fetching all categorys: {content}")
        category = None
        # category = Category.query.all()
        category_query = db.session.query(Category)
        if not content.get("include_deleted"):
            category_query = category_query.filter(Category.deleted_by.is_(None))
        category = category_query.all()
        if not category:
            logger.debug("No categorys found")
            return False, None
        logger.success(f"Categorys fetched: {category}")
        return True, category
    except Exception as ex:
        logger.exception(f"Error fetching all categorys: {ex}")
        raise ex


def _delete_category(category):
    try:
        logger.debug(f"Deleting category: {category}")
        # Category.query.filter_by(category_id=category.category_id).delete()
        db.session.query(Category).filter_by(category_id=category.category_id).delete()
        db.session.commit()
        logger.success(f"Category deleted: {category}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting category: {ex}")
        db.session.rollback()
        return ex


def _add_category(category):
    try:
        logger.debug(f"Adding category: {category}")
        db.session.add(category)
        db.session.commit()
        db.session.refresh(category)
        category_dict = category.to_dict()
        logger.success(f"Category added: {category_dict}")
        return True, category
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding category: {ex}")
        db.session.rollback()
        raise ex


def _update_category(category):
    try:
        logger.debug(f"Updating category: {category}")
        updated_category = None
        # Category.query.filter_by(category_id=category.category_id).update(category.to_dict())
        updated_category = db.session.merge(category)
        db.session.commit()
        if not updated_category:
            logger.exception("Category not updated")
            return False, None
        updated_category_dict = updated_category.to_dict()
        logger.success(f"Category updated: {updated_category_dict}")
        return True, updated_category_dict
    except Exception as ex:
        logger.exception(f"Error updating category: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region CategoryProvider Helper Functions
def _get_category_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching category by attribute {attribute_name}: {content}")
        category = None
        category_query = db.session.query(Category).filter(
            getattr(Category, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            category_query = category_query.filter(Category.deleted_by.is_(None))
        category = category_query.first()
        if not category:
            logger.debug(
                f"No category found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        category_dict = category.to_dict()
        logger.success(
            f"Category fetched by attribute {attribute_name}: {category_dict}"
        )
        return True, category
    except Exception as ex:
        logger.exception(f"Error fetching category by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_category_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective category data by attribute {attribute_name}: {content}"
        )
        categorys_dict = None
        categorys = (
            db.session.query(Category)
            .filter(
                getattr(Category, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            categorys_dict = {
                getattr(category_data, attribute_name): category_data
                for category_data in categorys
            }
        else:
            categorys_dict = {
                getattr(category_data, attribute_name): category_data.to_dict()
                for category_data in categorys
            }
        if not categorys_dict:
            logger.debug(
                f"No categorys found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"Categorys fetched by attribute {attribute_name}: {categorys_dict}"
        )
        return True, categorys_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective category data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

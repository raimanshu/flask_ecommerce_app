from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class ProductImage(db.Model):
    __tablename__ = "product_image"

    product_image_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("product.product_id"), nullable=False)
    # product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    image_url = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    alt_text = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    is_main = db.Column(db.Boolean, default=False)
    attributes = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    modified_at = db.Column(
        db.DateTime,
        nullable=True,
    )
    modified_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)

    def to_dict(self):
        return {
            "product_image_id": self.product_image_id,
            "product_id": self.product_id,
            "image_url": self.image_url,
            "alt_text": self.alt_text,
            "is_main": self.is_main,
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
            logger.debug(f"Adding product_image: {self} to product_image table")
            return _add_product_image(self)
        except Exception as e:
            logger.exception(f"Error adding product_image: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating product_image: {self} to product_image table")
            return _update_product_image(self)
        except Exception as e:
            logger.exception(f"Error updating product_image: {e}")
            return False, None

    def delete(product_image):
        try:
            logger.debug(
                f"Deleting product_image: {product_image} from product_image table"
            )
            return _delete_product_image(product_image)
        except Exception as e:
            logger.exception(f"Error deleting product_image: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching product_image: {content} from product_image table")
            return _get_product_image(content)
        except Exception as ex:
            logger.exception(f"Error fetching product_image: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all product_images from product_image table")
            return _get_all_product_images(content)
        except Exception as ex:
            logger.exception(f"Error fetching all product_images: {ex}")
            return False, None


class ProductImageProvider(ProductImage):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(
                f"Fetching product_image by attribute {attribute_name}: {content}"
            )
            return _get_product_image_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in ProductImageProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_product_image_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in ProductImageProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region ProductImage Helper Functions


def _get_product_image(content):
    try:
        logger.debug(f"Fetching product_image: {content}")
        if content.get("product_image", ""):
            content["product_image_id"] = content["product_image"].product_image_id
        elif content.get("entity_id", ""):
            content["product_image_id"] = content["entity_id"]
        product_image = None
        # product_image = ProductImage.query.filter_by(product_image_id=content["product_image_id"]).first()
        product_image_query = db.session.query(ProductImage).filter_by(
            product_image_id=content["product_image_id"]
        )
        if not content.get("include_deleted"):
            product_image_query = product_image_query.filter(
                ProductImage.deleted_by.is_(None)
            )
        product_image = product_image_query.first()
        if not product_image:
            logger.debug("ProductImage not found")
            return False, None
        product_image_dict = product_image.to_dict()
        logger.success(f"ProductImage fetched: {product_image_dict}")
        return True, product_image_dict
    except Exception as ex:
        logger.exception(f"Error fetching product_image: {ex}")
        raise ex


def _get_all_product_images(content):
    try:
        logger.debug(f"Fetching all product_images: {content}")
        product_image = None
        # product_image = ProductImage.query.all()
        product_image_query = db.session.query(ProductImage)
        if not content.get("include_deleted"):
            product_image_query = product_image_query.filter(
                ProductImage.deleted_by.is_(None)
            )
        product_image = product_image_query.all()
        if not product_image:
            logger.debug("No product_images found")
            return False, None
        logger.success(f"ProductImages fetched: {product_image}")
        return True, product_image
    except Exception as ex:
        logger.exception(f"Error fetching all product_images: {ex}")
        raise ex


def _delete_product_image(product_image):
    try:
        logger.debug(f"Deleting product_image: {product_image}")
        # ProductImage.query.filter_by(product_image_id=product_image.product_image_id).delete()
        db.session.query(ProductImage).filter_by(
            product_image_id=product_image.product_image_id
        ).delete()
        db.session.commit()
        logger.success(f"ProductImage deleted: {product_image}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting product_image: {ex}")
        db.session.rollback()
        return ex


def _add_product_image(product_image):
    try:
        logger.debug(f"Adding product_image: {product_image}")
        db.session.add(product_image)
        db.session.commit()
        db.session.refresh(product_image)
        product_image_dict = product_image.to_dict()
        logger.success(f"ProductImage added: {product_image_dict}")
        return True, product_image
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding product_image: {ex}")
        db.session.rollback()
        raise ex


def _update_product_image(product_image):
    try:
        logger.debug(f"Updating product_image: {product_image}")
        updated_product_image = None
        # ProductImage.query.filter_by(product_image_id=product_image.product_image_id).update(product_image.to_dict())
        updated_product_image = db.session.merge(product_image)
        db.session.commit()
        if not updated_product_image:
            logger.exception("ProductImage not updated")
            return False, None
        updated_product_image_dict = updated_product_image.to_dict()
        logger.success(f"ProductImage updated: {updated_product_image_dict}")
        return True, updated_product_image_dict
    except Exception as ex:
        logger.exception(f"Error updating product_image: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region ProductImageProvider Helper Functions
def _get_product_image_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching product_image by attribute {attribute_name}: {content}")
        product_image = None
        product_image_query = db.session.query(ProductImage).filter(
            getattr(ProductImage, attribute_name)
            == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            product_image_query = product_image_query.filter(
                ProductImage.deleted_by.is_(None)
            )
        product_image = product_image_query.first()
        if not product_image:
            logger.debug(
                f"No product_image found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        product_image_dict = product_image.to_dict()
        logger.success(
            f"ProductImage fetched by attribute {attribute_name}: {product_image_dict}"
        )
        return True, product_image
    except Exception as ex:
        logger.exception(
            f"Error fetching product_image by attribute {attribute_name}: {ex}"
        )
        raise ex


def _get_collective_product_image_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective product_image data by attribute {attribute_name}: {content}"
        )
        product_images_dict = None
        product_images = (
            db.session.query(ProductImage)
            .filter(
                getattr(ProductImage, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            product_images_dict = {
                getattr(product_image_data, attribute_name): product_image_data
                for product_image_data in product_images
            }
        else:
            product_images_dict = {
                getattr(
                    product_image_data, attribute_name
                ): product_image_data.to_dict()
                for product_image_data in product_images
            }
        if not product_images_dict:
            logger.debug(
                f"No product_images found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"ProductImages fetched by attribute {attribute_name}: {product_images_dict}"
        )
        return True, product_images_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective product_image data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

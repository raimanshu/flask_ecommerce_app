from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Product(db.Model):
    __tablename__ = "product"

    product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    name = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    slug = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    brand_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("brand.brand_id"), nullable=True)
    category_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("category.category_id"), nullable=True)
    # brand_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    # category_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    sku = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
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

    inventory = db.relationship('ProductInventory', uselist=False, backref='product')
    images = db.relationship('ProductImage', backref='product')
    reviews = db.relationship('Review', backref='product')
    cart_items = db.relationship('CartItem', backref='product')
    order_items = db.relationship('OrderItem', backref='product')

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "brand_id": self.brand_id,
            "category_id": self.category_id,
            "price": self.price,
            "discount_price": self.discount_price,
            "sku": self.is_actskuive,
            "is_active": self.is_active,
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
            logger.debug(f"Adding product: {self} to product table")
            return _add_product(self)
        except Exception as e:
            logger.exception(f"Error adding product: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating product: {self} to product table")
            return _update_product(self)
        except Exception as e:
            logger.exception(f"Error updating product: {e}")
            return False, None

    def delete(product):
        try:
            logger.debug(f"Deleting product: {product} from product table")
            return _delete_product(product)
        except Exception as e:
            logger.exception(f"Error deleting product: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching product: {content} from product table")
            return _get_product(content)
        except Exception as ex:
            logger.exception(f"Error fetching product: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all products from product table")
            return _get_all_products(content)
        except Exception as ex:
            logger.exception(f"Error fetching all products: {ex}")
            return False, None


class ProductProvider(Product):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching product by attribute {attribute_name}: {content}")
            return _get_product_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in ProductProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_product_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in ProductProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Product Helper Functions


def _get_product(content):
    try:
        logger.debug(f"Fetching product: {content}")
        if content.get("product", ""):
            content["product_id"] = content["product"].product_id
        elif content.get("entity_id", ""):
            content["product_id"] = content["entity_id"]
        product = None
        # product = Product.query.filter_by(product_id=content["product_id"]).first()
        product_query = db.session.query(Product).filter_by(
            product_id=content["product_id"]
        )
        if not content.get("include_deleted"):
            product_query = product_query.filter(Product.deleted_by.is_(None))
        product = product_query.first()
        if not product:
            logger.debug("Product not found")
            return False, None
        product_dict = product.to_dict()
        logger.success(f"Product fetched: {product_dict}")
        return True, product_dict
    except Exception as ex:
        logger.exception(f"Error fetching product: {ex}")
        raise ex


def _get_all_products(content):
    try:
        logger.debug(f"Fetching all products: {content}")
        product = None
        # product = Product.query.all()
        product_query = db.session.query(Product)
        if not content.get("include_deleted"):
            product_query = product_query.filter(Product.deleted_by.is_(None))
        product = product_query.all()
        if not product:
            logger.debug("No products found")
            return False, None
        logger.success(f"Products fetched: {product}")
        return True, product
    except Exception as ex:
        logger.exception(f"Error fetching all products: {ex}")
        raise ex


def _delete_product(product):
    try:
        logger.debug(f"Deleting product: {product}")
        # Product.query.filter_by(product_id=product.product_id).delete()
        db.session.query(Product).filter_by(product_id=product.product_id).delete()
        db.session.commit()
        logger.success(f"Product deleted: {product}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting product: {ex}")
        db.session.rollback()
        return ex


def _add_product(product):
    try:
        logger.debug(f"Adding product: {product}")
        db.session.add(product)
        db.session.commit()
        db.session.refresh(product)
        product_dict = product.to_dict()
        logger.success(f"Product added: {product_dict}")
        return True, product
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding product: {ex}")
        db.session.rollback()
        raise ex


def _update_product(product):
    try:
        logger.debug(f"Updating product: {product}")
        updated_product = None
        # Product.query.filter_by(product_id=product.product_id).update(product.to_dict())
        updated_product = db.session.merge(product)
        db.session.commit()
        if not updated_product:
            logger.exception("Product not updated")
            return False, None
        updated_product_dict = updated_product.to_dict()
        logger.success(f"Product updated: {updated_product_dict}")
        return True, updated_product_dict
    except Exception as ex:
        logger.exception(f"Error updating product: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region ProductProvider Helper Functions
def _get_product_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching product by attribute {attribute_name}: {content}")
        product = None
        product_query = db.session.query(Product).filter(
            getattr(Product, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            product_query = product_query.filter(Product.deleted_by.is_(None))
        product = product_query.first()
        if not product:
            logger.debug(
                f"No product found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        product_dict = product.to_dict()
        logger.success(f"Product fetched by attribute {attribute_name}: {product_dict}")
        return True, product
    except Exception as ex:
        logger.exception(f"Error fetching product by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_product_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective product data by attribute {attribute_name}: {content}"
        )
        products_dict = None
        products = (
            db.session.query(Product)
            .filter(
                getattr(Product, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            products_dict = {
                getattr(product_data, attribute_name): product_data
                for product_data in products
            }
        else:
            products_dict = {
                getattr(product_data, attribute_name): product_data.to_dict()
                for product_data in products
            }
        if not products_dict:
            logger.debug(
                f"No products found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"Products fetched by attribute {attribute_name}: {products_dict}"
        )
        return True, products_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective product data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

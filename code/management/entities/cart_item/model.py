from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class CartItem(db.Model):
    __tablename__ = "cart_item"

    cart_item_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    cart_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("cart.cart_id"), nullable=False)
    product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("product.product_id"), nullable=False)
    # cart_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    # product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp())
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
            "cart_item_id": self.cart_item_id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "added_at": self.added_at,
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
            logger.debug(f"Adding cart_item: {self} to cart_item table")
            return _add_cart_item(self)
        except Exception as e:
            logger.exception(f"Error adding cart_item: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating cart_item: {self} to cart_item table")
            return _update_cart_item(self)
        except Exception as e:
            logger.exception(f"Error updating cart_item: {e}")
            return False, None

    def delete(cart_item):
        try:
            logger.debug(f"Deleting cart_item: {cart_item} from cart_item table")
            return _delete_cart_item(cart_item)
        except Exception as e:
            logger.exception(f"Error deleting cart_item: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching cart_item: {content} from cart_item table")
            return _get_cart_item(content)
        except Exception as ex:
            logger.exception(f"Error fetching cart_item: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all cart_items from cart_item table")
            return _get_all_cart_items(content)
        except Exception as ex:
            logger.exception(f"Error fetching all cart_items: {ex}")
            return False, None


class CartItemProvider(CartItem):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching cart_item by attribute {attribute_name}: {content}")
            return _get_cart_item_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in CartItemProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_cart_item_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in CartItemProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region CartItem Helper Functions


def _get_cart_item(content):
    try:
        logger.debug(f"Fetching cart_item: {content}")
        if content.get("cart_item", ""):
            content["cart_item_id"] = content["cart_item"].cart_item_id
        elif content.get("entity_id", ""):
            content["cart_item_id"] = content["entity_id"]
        cart_item = None
        # cart_item = CartItem.query.filter_by(cart_item_id=content["cart_item_id"]).first()
        cart_item_query = db.session.query(CartItem).filter_by(
            cart_item_id=content["cart_item_id"]
        )
        if not content.get("include_deleted"):
            cart_item_query = cart_item_query.filter(CartItem.deleted_by.is_(None))
        cart_item = cart_item_query.first()
        if not cart_item:
            logger.debug("CartItem not found")
            return False, None
        cart_item_dict = cart_item.to_dict()
        logger.success(f"CartItem fetched: {cart_item_dict}")
        return True, cart_item_dict
    except Exception as ex:
        logger.exception(f"Error fetching cart_item: {ex}")
        raise ex


def _get_all_cart_items(content):
    try:
        logger.debug(f"Fetching all cart_items: {content}")
        cart_item = None
        # cart_item = CartItem.query.all()
        cart_item_query = db.session.query(CartItem)
        if not content.get("include_deleted"):
            cart_item_query = cart_item_query.filter(CartItem.deleted_by.is_(None))
        cart_item = cart_item_query.all()
        if not cart_item:
            logger.debug("No cart_items found")
            return False, None
        logger.success(f"CartItems fetched: {cart_item}")
        return True, cart_item
    except Exception as ex:
        logger.exception(f"Error fetching all cart_items: {ex}")
        raise ex


def _delete_cart_item(cart_item):
    try:
        logger.debug(f"Deleting cart_item: {cart_item}")
        # CartItem.query.filter_by(cart_item_id=cart_item.cart_item_id).delete()
        db.session.query(CartItem).filter_by(
            cart_item_id=cart_item.cart_item_id
        ).delete()
        db.session.commit()
        logger.success(f"CartItem deleted: {cart_item}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting cart_item: {ex}")
        db.session.rollback()
        return ex


def _add_cart_item(cart_item):
    try:
        logger.debug(f"Adding cart_item: {cart_item}")
        db.session.add(cart_item)
        db.session.commit()
        db.session.refresh(cart_item)
        cart_item_dict = cart_item.to_dict()
        logger.success(f"CartItem added: {cart_item_dict}")
        return True, cart_item
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding cart_item: {ex}")
        db.session.rollback()
        raise ex


def _update_cart_item(cart_item):
    try:
        logger.debug(f"Updating cart_item: {cart_item}")
        updated_cart_item = None
        # CartItem.query.filter_by(cart_item_id=cart_item.cart_item_id).update(cart_item.to_dict())
        updated_cart_item = db.session.merge(cart_item)
        db.session.commit()
        if not updated_cart_item:
            logger.exception("CartItem not updated")
            return False, None
        updated_cart_item_dict = updated_cart_item.to_dict()
        logger.success(f"CartItem updated: {updated_cart_item_dict}")
        return True, updated_cart_item_dict
    except Exception as ex:
        logger.exception(f"Error updating cart_item: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region CartItemProvider Helper Functions
def _get_cart_item_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching cart_item by attribute {attribute_name}: {content}")
        cart_item = None
        cart_item_query = db.session.query(CartItem).filter(
            getattr(CartItem, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            cart_item_query = cart_item_query.filter(CartItem.deleted_by.is_(None))
        cart_item = cart_item_query.first()
        if not cart_item:
            logger.debug(
                f"No cart_item found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        cart_item_dict = cart_item.to_dict()
        logger.success(
            f"CartItem fetched by attribute {attribute_name}: {cart_item_dict}"
        )
        return True, cart_item
    except Exception as ex:
        logger.exception(
            f"Error fetching cart_item by attribute {attribute_name}: {ex}"
        )
        raise ex


def _get_collective_cart_item_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective cart_item data by attribute {attribute_name}: {content}"
        )
        cart_items_dict = None
        cart_items = (
            db.session.query(CartItem)
            .filter(
                getattr(CartItem, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            cart_items_dict = {
                getattr(cart_item_data, attribute_name): cart_item_data
                for cart_item_data in cart_items
            }
        else:
            cart_items_dict = {
                getattr(cart_item_data, attribute_name): cart_item_data.to_dict()
                for cart_item_data in cart_items
            }
        if not cart_items_dict:
            logger.debug(
                f"No cart_items found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"CartItems fetched by attribute {attribute_name}: {cart_items_dict}"
        )
        return True, cart_items_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective cart_item data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

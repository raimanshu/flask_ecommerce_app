from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Cart(db.Model):
    __tablename__ = "cart"

    cart_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("user.user_id"), nullable=False)
    # user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
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

    items = db.relationship('CartItem', backref='cart')

    def to_dict(self):
        return {
            "cart_id": self.cart_id,
            "user_id": self.user_id,
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
            logger.debug(f"Adding cart: {self} to cart table")
            return _add_cart(self)
        except Exception as e:
            logger.exception(f"Error adding cart: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating cart: {self} to cart table")
            return _update_cart(self)
        except Exception as e:
            logger.exception(f"Error updating cart: {e}")
            return False, None

    def delete(cart):
        try:
            logger.debug(f"Deleting cart: {cart} from cart table")
            return _delete_cart(cart)
        except Exception as e:
            logger.exception(f"Error deleting cart: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching cart: {content} from cart table")
            return _get_cart(content)
        except Exception as ex:
            logger.exception(f"Error fetching cart: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all carts from cart table")
            return _get_all_carts(content)
        except Exception as ex:
            logger.exception(f"Error fetching all carts: {ex}")
            return False, None


class CartProvider(Cart):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching cart by attribute {attribute_name}: {content}")
            return _get_cart_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in CartProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_cart_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in CartProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Cart Helper Functions


def _get_cart(content):
    try:
        logger.debug(f"Fetching cart: {content}")
        if content.get("cart", ""):
            content["cart_id"] = content["cart"].cart_id
        elif content.get("entity_id", ""):
            content["cart_id"] = content["entity_id"]
        cart = None
        # cart = Cart.query.filter_by(cart_id=content["cart_id"]).first()
        cart_query = db.session.query(Cart).filter_by(cart_id=content["cart_id"])
        if not content.get("include_deleted"):
            cart_query = cart_query.filter(Cart.deleted_by.is_(None))
        cart = cart_query.first()
        if not cart:
            logger.debug("Cart not found")
            return False, None
        cart_dict = cart.to_dict()
        logger.success(f"Cart fetched: {cart_dict}")
        return True, cart_dict
    except Exception as ex:
        logger.exception(f"Error fetching cart: {ex}")
        raise ex


def _get_all_carts(content):
    try:
        logger.debug(f"Fetching all carts: {content}")
        cart = None
        # cart = Cart.query.all()
        cart_query = db.session.query(Cart)
        if not content.get("include_deleted"):
            cart_query = cart_query.filter(Cart.deleted_by.is_(None))
        cart = cart_query.all()
        if not cart:
            logger.debug("No carts found")
            return False, None
        logger.success(f"Carts fetched: {cart}")
        return True, cart
    except Exception as ex:
        logger.exception(f"Error fetching all carts: {ex}")
        raise ex


def _delete_cart(cart):
    try:
        logger.debug(f"Deleting cart: {cart}")
        # Cart.query.filter_by(cart_id=cart.cart_id).delete()
        db.session.query(Cart).filter_by(cart_id=cart.cart_id).delete()
        db.session.commit()
        logger.success(f"Cart deleted: {cart}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting cart: {ex}")
        db.session.rollback()
        return ex


def _add_cart(cart):
    try:
        logger.debug(f"Adding cart: {cart}")
        db.session.add(cart)
        db.session.commit()
        db.session.refresh(cart)
        cart_dict = cart.to_dict()
        logger.success(f"Cart added: {cart_dict}")
        return True, cart
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding cart: {ex}")
        db.session.rollback()
        raise ex


def _update_cart(cart):
    try:
        logger.debug(f"Updating cart: {cart}")
        updated_cart = None
        # Cart.query.filter_by(cart_id=cart.cart_id).update(cart.to_dict())
        updated_cart = db.session.merge(cart)
        db.session.commit()
        if not updated_cart:
            logger.exception("Cart not updated")
            return False, None
        updated_cart_dict = updated_cart.to_dict()
        logger.success(f"Cart updated: {updated_cart_dict}")
        return True, updated_cart_dict
    except Exception as ex:
        logger.exception(f"Error updating cart: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region CartProvider Helper Functions
def _get_cart_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching cart by attribute {attribute_name}: {content}")
        cart = None
        cart_query = db.session.query(Cart).filter(
            getattr(Cart, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            cart_query = cart_query.filter(Cart.deleted_by.is_(None))
        cart = cart_query.first()
        if not cart:
            logger.debug(
                f"No cart found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        cart_dict = cart.to_dict()
        logger.success(f"Cart fetched by attribute {attribute_name}: {cart_dict}")
        return True, cart
    except Exception as ex:
        logger.exception(f"Error fetching cart by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_cart_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective cart data by attribute {attribute_name}: {content}"
        )
        carts_dict = None
        carts = (
            db.session.query(Cart)
            .filter(
                getattr(Cart, attribute_name).in_(content.get(f"{attribute_name}", []))
            )
            .all()
        )
        if require_object:
            carts_dict = {
                getattr(cart_data, attribute_name): cart_data for cart_data in carts
            }
        else:
            carts_dict = {
                getattr(cart_data, attribute_name): cart_data.to_dict()
                for cart_data in carts
            }
        if not carts_dict:
            logger.debug(
                f"No carts found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(f"Carts fetched by attribute {attribute_name}: {carts_dict}")
        return True, carts_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective cart data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

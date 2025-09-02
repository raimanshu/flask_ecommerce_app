from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Order(db.Model):
    __tablename__ = "order"

    order_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("user.user_id"), nullable=False)
    # user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    order_number = db.Column(
        db.String(DB_COLUMN_MAX_LENGTH), nullable=False, unique=True
    )
    total_amount = db.Column(db.Float, nullable=False)
    shipping_fee = db.Column(db.Float, nullable=True)
    discount_amount = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    order_status = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    shipping_address_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("address_book.address_book_id"), nullable=True)
    billing_address_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("address_book.address_book_id"), nullable=True)
    # shipping_address_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    # billing_address_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
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

    items = db.relationship('OrderItem', backref='order')
    payment = db.relationship('Payment', uselist=False, backref='order')
    shipping = db.relationship('Shipping', uselist=False, backref='order')

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "order_number": self.order_number,
            "total_amount": self.total_amount,
            "shipping_fee": self.shipping_fee,
            "discount_amount": self.discount_amount,
            "payment_status": self.payment_status,
            "order_status": self.order_status,
            "shipping_address_id": self.shipping_address_id,
            "billing_address_id": self.billing_address_id,
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
            logger.debug(f"Adding order: {self} to order table")
            return _add_order(self)
        except Exception as e:
            logger.exception(f"Error adding order: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating order: {self} to order table")
            return _update_order(self)
        except Exception as e:
            logger.exception(f"Error updating order: {e}")
            return False, None

    def delete(order):
        try:
            logger.debug(f"Deleting order: {order} from order table")
            return _delete_order(order)
        except Exception as e:
            logger.exception(f"Error deleting order: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching order: {content} from order table")
            return _get_order(content)
        except Exception as ex:
            logger.exception(f"Error fetching order: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all orders from order table")
            return _get_all_orders(content)
        except Exception as ex:
            logger.exception(f"Error fetching all orders: {ex}")
            return False, None


class OrderProvider(Order):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching order by attribute {attribute_name}: {content}")
            return _get_order_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in OrderProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_order_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in OrderProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Order Helper Functions


def _get_order(content):
    try:
        logger.debug(f"Fetching order: {content}")
        if content.get("order", ""):
            content["order_id"] = content["order"].order_id
        elif content.get("entity_id", ""):
            content["order_id"] = content["entity_id"]
        order = None
        # order = Order.query.filter_by(order_id=content["order_id"]).first()
        order_query = db.session.query(Order).filter_by(order_id=content["order_id"])
        if not content.get("include_deleted"):
            order_query = order_query.filter(Order.deleted_by.is_(None))
        order = order_query.first()
        if not order:
            logger.debug("Order not found")
            return False, None
        order_dict = order.to_dict()
        logger.success(f"Order fetched: {order_dict}")
        return True, order_dict
    except Exception as ex:
        logger.exception(f"Error fetching order: {ex}")
        raise ex


def _get_all_orders(content):
    try:
        logger.debug(f"Fetching all orders: {content}")
        order = None
        # order = Order.query.all()
        order_query = db.session.query(Order)
        if not content.get("include_deleted"):
            order_query = order_query.filter(Order.deleted_by.is_(None))
        order = order_query.all()
        if not order:
            logger.debug("No orders found")
            return False, None
        logger.success(f"Orders fetched: {order}")
        return True, order
    except Exception as ex:
        logger.exception(f"Error fetching all orders: {ex}")
        raise ex


def _delete_order(order):
    try:
        logger.debug(f"Deleting order: {order}")
        # Order.query.filter_by(order_id=order.order_id).delete()
        db.session.query(Order).filter_by(order_id=order.order_id).delete()
        db.session.commit()
        logger.success(f"Order deleted: {order}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting order: {ex}")
        db.session.rollback()
        return ex


def _add_order(order):
    try:
        logger.debug(f"Adding order: {order}")
        db.session.add(order)
        db.session.commit()
        db.session.refresh(order)
        order_dict = order.to_dict()
        logger.success(f"Order added: {order_dict}")
        return True, order
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding order: {ex}")
        db.session.rollback()
        raise ex


def _update_order(order):
    try:
        logger.debug(f"Updating order: {order}")
        updated_order = None
        # Order.query.filter_by(order_id=order.order_id).update(order.to_dict())
        updated_order = db.session.merge(order)
        db.session.commit()
        if not updated_order:
            logger.exception("Order not updated")
            return False, None
        updated_order_dict = updated_order.to_dict()
        logger.success(f"Order updated: {updated_order_dict}")
        return True, updated_order_dict
    except Exception as ex:
        logger.exception(f"Error updating order: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region OrderProvider Helper Functions
def _get_order_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching order by attribute {attribute_name}: {content}")
        order = None
        order_query = db.session.query(Order).filter(
            getattr(Order, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            order_query = order_query.filter(Order.deleted_by.is_(None))
        order = order_query.first()
        if not order:
            logger.debug(
                f"No order found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        order_dict = order.to_dict()
        logger.success(f"Order fetched by attribute {attribute_name}: {order_dict}")
        return True, order
    except Exception as ex:
        logger.exception(f"Error fetching order by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_order_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective order data by attribute {attribute_name}: {content}"
        )
        orders_dict = None
        orders = (
            db.session.query(Order)
            .filter(
                getattr(Order, attribute_name).in_(content.get(f"{attribute_name}", []))
            )
            .all()
        )
        if require_object:
            orders_dict = {
                getattr(order_data, attribute_name): order_data for order_data in orders
            }
        else:
            orders_dict = {
                getattr(order_data, attribute_name): order_data.to_dict()
                for order_data in orders
            }
        if not orders_dict:
            logger.debug(
                f"No orders found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(f"Orders fetched by attribute {attribute_name}: {orders_dict}")
        return True, orders_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective order data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

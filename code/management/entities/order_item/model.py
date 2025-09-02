from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class OrderItem(db.Model):
    __tablename__ = "order_item"

    order_item_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    order_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("order.order_id"), nullable=False)
    product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("product.product_id"), nullable=False)
    # order_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    # product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
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
            "order_item_id": self.order_item_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
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
            logger.debug(f"Adding order_item: {self} to order_item table")
            return _add_order_item(self)
        except Exception as e:
            logger.exception(f"Error adding order_item: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating order_item: {self} to order_item table")
            return _update_order_item(self)
        except Exception as e:
            logger.exception(f"Error updating order_item: {e}")
            return False, None

    def delete(order_item):
        try:
            logger.debug(f"Deleting order_item: {order_item} from order_item table")
            return _delete_order_item(order_item)
        except Exception as e:
            logger.exception(f"Error deleting order_item: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching order_item: {content} from order_item table")
            return _get_order_item(content)
        except Exception as ex:
            logger.exception(f"Error fetching order_item: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all order_items from order_item table")
            return _get_all_order_items(content)
        except Exception as ex:
            logger.exception(f"Error fetching all order_items: {ex}")
            return False, None


class OrderItemProvider(OrderItem):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(
                f"Fetching order_item by attribute {attribute_name}: {content}"
            )
            return _get_order_item_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in OrderItemProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_order_item_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in OrderItemProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region OrderItem Helper Functions


def _get_order_item(content):
    try:
        logger.debug(f"Fetching order_item: {content}")
        if content.get("order_item", ""):
            content["order_item_id"] = content["order_item"].order_item_id
        elif content.get("entity_id", ""):
            content["order_item_id"] = content["entity_id"]
        order_item = None
        # order_item = OrderItem.query.filter_by(order_item_id=content["order_item_id"]).first()
        order_item_query = db.session.query(OrderItem).filter_by(
            order_item_id=content["order_item_id"]
        )
        if not content.get("include_deleted"):
            order_item_query = order_item_query.filter(OrderItem.deleted_by.is_(None))
        order_item = order_item_query.first()
        if not order_item:
            logger.debug("OrderItem not found")
            return False, None
        order_item_dict = order_item.to_dict()
        logger.success(f"OrderItem fetched: {order_item_dict}")
        return True, order_item_dict
    except Exception as ex:
        logger.exception(f"Error fetching order_item: {ex}")
        raise ex


def _get_all_order_items(content):
    try:
        logger.debug(f"Fetching all order_items: {content}")
        order_item = None
        # order_item = OrderItem.query.all()
        order_item_query = db.session.query(OrderItem)
        if not content.get("include_deleted"):
            order_item_query = order_item_query.filter(OrderItem.deleted_by.is_(None))
        order_item = order_item_query.all()
        if not order_item:
            logger.debug("No order_items found")
            return False, None
        logger.success(f"OrderItems fetched: {order_item}")
        return True, order_item
    except Exception as ex:
        logger.exception(f"Error fetching all order_items: {ex}")
        raise ex


def _delete_order_item(order_item):
    try:
        logger.debug(f"Deleting order_item: {order_item}")
        # OrderItem.query.filter_by(order_item_id=order_item.order_item_id).delete()
        db.session.query(OrderItem).filter_by(
            order_item_id=order_item.order_item_id
        ).delete()
        db.session.commit()
        logger.success(f"OrderItem deleted: {order_item}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting order_item: {ex}")
        db.session.rollback()
        return ex


def _add_order_item(order_item):
    try:
        logger.debug(f"Adding order_item: {order_item}")
        db.session.add(order_item)
        db.session.commit()
        db.session.refresh(order_item)
        order_item_dict = order_item.to_dict()
        logger.success(f"OrderItem added: {order_item_dict}")
        return True, order_item
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding order_item: {ex}")
        db.session.rollback()
        raise ex


def _update_order_item(order_item):
    try:
        logger.debug(f"Updating order_item: {order_item}")
        updated_order_item = None
        # OrderItem.query.filter_by(order_item_id=order_item.order_item_id).update(order_item.to_dict())
        updated_order_item = db.session.merge(order_item)
        db.session.commit()
        if not updated_order_item:
            logger.exception("OrderItem not updated")
            return False, None
        updated_order_item_dict = updated_order_item.to_dict()
        logger.success(f"OrderItem updated: {updated_order_item_dict}")
        return True, updated_order_item_dict
    except Exception as ex:
        logger.exception(f"Error updating order_item: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region OrderItemProvider Helper Functions
def _get_order_item_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching order_item by attribute {attribute_name}: {content}")
        order_item = None
        order_item_query = db.session.query(OrderItem).filter(
            getattr(OrderItem, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            order_item_query = order_item_query.filter(OrderItem.deleted_by.is_(None))
        order_item = order_item_query.first()
        if not order_item:
            logger.debug(
                f"No order_item found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        order_item_dict = order_item.to_dict()
        logger.success(
            f"OrderItem fetched by attribute {attribute_name}: {order_item_dict}"
        )
        return True, order_item
    except Exception as ex:
        logger.exception(
            f"Error fetching order_item by attribute {attribute_name}: {ex}"
        )
        raise ex


def _get_collective_order_item_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective order_item data by attribute {attribute_name}: {content}"
        )
        order_items_dict = None
        order_items = (
            db.session.query(OrderItem)
            .filter(
                getattr(OrderItem, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            order_items_dict = {
                getattr(order_item_data, attribute_name): order_item_data
                for order_item_data in order_items
            }
        else:
            order_items_dict = {
                getattr(order_item_data, attribute_name): order_item_data.to_dict()
                for order_item_data in order_items
            }
        if not order_items_dict:
            logger.debug(
                f"No order_items found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"OrderItems fetched by attribute {attribute_name}: {order_items_dict}"
        )
        return True, order_items_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective order_item data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

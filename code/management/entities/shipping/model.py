from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Shipping(db.Model):
    __tablename__ = "shipping"

    shipping_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    order_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("order.order_id"), nullable=False)
    # order_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    courier_name = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    tracking_number = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
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

    #
    def to_dict(self):
        return {
            "shipping_id": self.shipping_id,
            "order_id": self.order_id,
            "courier_name": self.courier_name,
            "tracking_number": self.tracking_number,
            "shipped_at": self.shipped_at,
            "delivered_at": self.delivered_at,
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
            logger.debug(f"Adding shipping: {self} to shipping table")
            return _add_shipping(self)
        except Exception as e:
            logger.exception(f"Error adding shipping: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating shipping: {self} to shipping table")
            return _update_shipping(self)
        except Exception as e:
            logger.exception(f"Error updating shipping: {e}")
            return False, None

    def delete(shipping):
        try:
            logger.debug(f"Deleting shipping: {shipping} from shipping table")
            return _delete_shipping(shipping)
        except Exception as e:
            logger.exception(f"Error deleting shipping: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching shipping: {content} from shipping table")
            return _get_shipping(content)
        except Exception as ex:
            logger.exception(f"Error fetching shipping: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all shippings from shipping table")
            return _get_all_shippings(content)
        except Exception as ex:
            logger.exception(f"Error fetching all shippings: {ex}")
            return False, None


class ShippingProvider(Shipping):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching shipping by attribute {attribute_name}: {content}")
            return _get_shipping_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in ShippingProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_shipping_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in ShippingProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Shipping Helper Functions


def _get_shipping(content):
    try:
        logger.debug(f"Fetching shipping: {content}")
        if content.get("shipping", ""):
            content["shipping_id"] = content["shipping"].shipping_id
        elif content.get("entity_id", ""):
            content["shipping_id"] = content["entity_id"]
        shipping = None
        # shipping = Shipping.query.filter_by(shipping_id=content["shipping_id"]).first()
        shipping_query = db.session.query(Shipping).filter_by(
            shipping_id=content["shipping_id"]
        )
        if not content.get("include_deleted"):
            shipping_query = shipping_query.filter(Shipping.deleted_by.is_(None))
        shipping = shipping_query.first()
        if not shipping:
            logger.debug("Shipping not found")
            return False, None
        shipping_dict = shipping.to_dict()
        logger.success(f"Shipping fetched: {shipping_dict}")
        return True, shipping_dict
    except Exception as ex:
        logger.exception(f"Error fetching shipping: {ex}")
        raise ex


def _get_all_shippings(content):
    try:
        logger.debug(f"Fetching all shippings: {content}")
        shipping = None
        # shipping = Shipping.query.all()
        shipping_query = db.session.query(Shipping)
        if not content.get("include_deleted"):
            shipping_query = shipping_query.filter(Shipping.deleted_by.is_(None))
        shipping = shipping_query.all()
        if not shipping:
            logger.debug("No shippings found")
            return False, None
        logger.success(f"Shippings fetched: {shipping}")
        return True, shipping
    except Exception as ex:
        logger.exception(f"Error fetching all shippings: {ex}")
        raise ex


def _delete_shipping(shipping):
    try:
        logger.debug(f"Deleting shipping: {shipping}")
        # Shipping.query.filter_by(shipping_id=shipping.shipping_id).delete()
        db.session.query(Shipping).filter_by(shipping_id=shipping.shipping_id).delete()
        db.session.commit()
        logger.success(f"Shipping deleted: {shipping}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting shipping: {ex}")
        db.session.rollback()
        return ex


def _add_shipping(shipping):
    try:
        logger.debug(f"Adding shipping: {shipping}")
        db.session.add(shipping)
        db.session.commit()
        db.session.refresh(shipping)
        shipping_dict = shipping.to_dict()
        logger.success(f"Shipping added: {shipping_dict}")
        return True, shipping
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding shipping: {ex}")
        db.session.rollback()
        raise ex


def _update_shipping(shipping):
    try:
        logger.debug(f"Updating shipping: {shipping}")
        updated_shipping = None
        # Shipping.query.filter_by(shipping_id=shipping.shipping_id).update(shipping.to_dict())
        updated_shipping = db.session.merge(shipping)
        db.session.commit()
        if not updated_shipping:
            logger.exception("Shipping not updated")
            return False, None
        updated_shipping_dict = updated_shipping.to_dict()
        logger.success(f"Shipping updated: {updated_shipping_dict}")
        return True, updated_shipping_dict
    except Exception as ex:
        logger.exception(f"Error updating shipping: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region ShippingProvider Helper Functions
def _get_shipping_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching shipping by attribute {attribute_name}: {content}")
        shipping = None
        shipping_query = db.session.query(Shipping).filter(
            getattr(Shipping, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            shipping_query = shipping_query.filter(Shipping.deleted_by.is_(None))
        shipping = shipping_query.first()
        if not shipping:
            logger.debug(
                f"No shipping found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        shipping_dict = shipping.to_dict()
        logger.success(
            f"Shipping fetched by attribute {attribute_name}: {shipping_dict}"
        )
        return True, shipping
    except Exception as ex:
        logger.exception(f"Error fetching shipping by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_shipping_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective shipping data by attribute {attribute_name}: {content}"
        )
        shippings_dict = None
        shippings = (
            db.session.query(Shipping)
            .filter(
                getattr(Shipping, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            shippings_dict = {
                getattr(shipping_data, attribute_name): shipping_data
                for shipping_data in shippings
            }
        else:
            shippings_dict = {
                getattr(shipping_data, attribute_name): shipping_data.to_dict()
                for shipping_data in shippings
            }
        if not shippings_dict:
            logger.debug(
                f"No shippings found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"Shippings fetched by attribute {attribute_name}: {shippings_dict}"
        )
        return True, shippings_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective shipping data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

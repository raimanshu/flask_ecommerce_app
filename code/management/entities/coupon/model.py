from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Coupon(db.Model):
    __tablename__ = "coupon"

    coupon_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    code = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False, unique=True)
    discount_value = db.Column(db.Float, nullable=False)
    min_order_value = db.Column(db.Float, nullable=True)
    max_discount = db.Column(db.Float, nullable=True)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
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
            "coupon_id": self.coupon_id,
            "code": self.code,
            "discount_value": self.discount_value,
            "min_order_value": self.email,
            "max_discount": self.max_discount,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "is_active": self.is_active,
            "usage_limit": self.usage_limit,
            "usage_count": self.usage_count,
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
            logger.debug(f"Adding coupon: {self} to coupon table")
            return _add_coupon(self)
        except Exception as e:
            logger.exception(f"Error adding coupon: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating coupon: {self} to coupon table")
            return _update_coupon(self)
        except Exception as e:
            logger.exception(f"Error updating coupon: {e}")
            return False, None

    def delete(coupon):
        try:
            logger.debug(f"Deleting coupon: {coupon} from coupon table")
            return _delete_coupon(coupon)
        except Exception as e:
            logger.exception(f"Error deleting coupon: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching coupon: {content} from coupon table")
            return _get_coupon(content)
        except Exception as ex:
            logger.exception(f"Error fetching coupon: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all coupons from coupon table")
            return _get_all_coupons(content)
        except Exception as ex:
            logger.exception(f"Error fetching all coupons: {ex}")
            return False, None


class CouponProvider(Coupon):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching coupon by attribute {attribute_name}: {content}")
            return _get_coupon_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in CouponProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_coupon_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in CouponProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Coupon Helper Functions


def _get_coupon(content):
    try:
        logger.debug(f"Fetching coupon: {content}")
        if content.get("coupon", ""):
            content["coupon_id"] = content["coupon"].coupon_id
        elif content.get("entity_id", ""):
            content["coupon_id"] = content["entity_id"]
        coupon = None
        # coupon = Coupon.query.filter_by(coupon_id=content["coupon_id"]).first()
        coupon_query = db.session.query(Coupon).filter_by(
            coupon_id=content["coupon_id"]
        )
        if not content.get("include_deleted"):
            coupon_query = coupon_query.filter(Coupon.deleted_by.is_(None))
        coupon = coupon_query.first()
        if not coupon:
            logger.debug("Coupon not found")
            return False, None
        coupon_dict = coupon.to_dict()
        logger.success(f"Coupon fetched: {coupon_dict}")
        return True, coupon_dict
    except Exception as ex:
        logger.exception(f"Error fetching coupon: {ex}")
        raise ex


def _get_all_coupons(content):
    try:
        logger.debug(f"Fetching all coupons: {content}")
        coupon = None
        # coupon = Coupon.query.all()
        coupon_query = db.session.query(Coupon)
        if not content.get("include_deleted"):
            coupon_query = coupon_query.filter(Coupon.deleted_by.is_(None))
        coupon = coupon_query.all()
        if not coupon:
            logger.debug("No coupons found")
            return False, None
        logger.success(f"Coupons fetched: {coupon}")
        return True, coupon
    except Exception as ex:
        logger.exception(f"Error fetching all coupons: {ex}")
        raise ex


def _delete_coupon(coupon):
    try:
        logger.debug(f"Deleting coupon: {coupon}")
        # Coupon.query.filter_by(coupon_id=coupon.coupon_id).delete()
        db.session.query(Coupon).filter_by(coupon_id=coupon.coupon_id).delete()
        db.session.commit()
        logger.success(f"Coupon deleted: {coupon}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting coupon: {ex}")
        db.session.rollback()
        return ex


def _add_coupon(coupon):
    try:
        logger.debug(f"Adding coupon: {coupon}")
        db.session.add(coupon)
        db.session.commit()
        db.session.refresh(coupon)
        coupon_dict = coupon.to_dict()
        logger.success(f"Coupon added: {coupon_dict}")
        return True, coupon
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding coupon: {ex}")
        db.session.rollback()
        raise ex


def _update_coupon(coupon):
    try:
        logger.debug(f"Updating coupon: {coupon}")
        updated_coupon = None
        # Coupon.query.filter_by(coupon_id=coupon.coupon_id).update(coupon.to_dict())
        updated_coupon = db.session.merge(coupon)
        db.session.commit()
        if not updated_coupon:
            logger.exception("Coupon not updated")
            return False, None
        updated_coupon_dict = updated_coupon.to_dict()
        logger.success(f"Coupon updated: {updated_coupon_dict}")
        return True, updated_coupon_dict
    except Exception as ex:
        logger.exception(f"Error updating coupon: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region CouponProvider Helper Functions
def _get_coupon_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching coupon by attribute {attribute_name}: {content}")
        coupon = None
        coupon_query = db.session.query(Coupon).filter(
            getattr(Coupon, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            coupon_query = coupon_query.filter(Coupon.deleted_by.is_(None))
        coupon = coupon_query.first()
        if not coupon:
            logger.debug(
                f"No coupon found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        coupon_dict = coupon.to_dict()
        logger.success(f"Coupon fetched by attribute {attribute_name}: {coupon_dict}")
        return True, coupon
    except Exception as ex:
        logger.exception(f"Error fetching coupon by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_coupon_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective coupon data by attribute {attribute_name}: {content}"
        )
        coupons_dict = None
        coupons = (
            db.session.query(Coupon)
            .filter(
                getattr(Coupon, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            coupons_dict = {
                getattr(coupon_data, attribute_name): coupon_data
                for coupon_data in coupons
            }
        else:
            coupons_dict = {
                getattr(coupon_data, attribute_name): coupon_data.to_dict()
                for coupon_data in coupons
            }
        if not coupons_dict:
            logger.debug(
                f"No coupons found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(f"Coupons fetched by attribute {attribute_name}: {coupons_dict}")
        return True, coupons_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective coupon data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

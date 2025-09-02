from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Payment(db.Model):
    __tablename__ = "payment"

    payment_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    order_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("order.order_id"), nullable=False)
    # order_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    payment_method = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    payment_reference = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)
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
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "amount": self.amount,
            "status": self.status,
            "paid_at": self.paid_at,
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
            logger.debug(f"Adding payment: {self} to payment table")
            return _add_payment(self)
        except Exception as e:
            logger.exception(f"Error adding payment: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating payment: {self} to payment table")
            return _update_payment(self)
        except Exception as e:
            logger.exception(f"Error updating payment: {e}")
            return False, None

    def delete(payment):
        try:
            logger.debug(f"Deleting payment: {payment} from payment table")
            return _delete_payment(payment)
        except Exception as e:
            logger.exception(f"Error deleting payment: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching payment: {content} from payment table")
            return _get_payment(content)
        except Exception as ex:
            logger.exception(f"Error fetching payment: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all payments from payment table")
            return _get_all_payments(content)
        except Exception as ex:
            logger.exception(f"Error fetching all payments: {ex}")
            return False, None


class PaymentProvider(Payment):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching payment by attribute {attribute_name}: {content}")
            return _get_payment_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in PaymentProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_payment_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in PaymentProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Payment Helper Functions


def _get_payment(content):
    try:
        logger.debug(f"Fetching payment: {content}")
        if content.get("payment", ""):
            content["payment_id"] = content["payment"].payment_id
        elif content.get("entity_id", ""):
            content["payment_id"] = content["entity_id"]
        payment = None
        # payment = Payment.query.filter_by(payment_id=content["payment_id"]).first()
        payment_query = db.session.query(Payment).filter_by(
            payment_id=content["payment_id"]
        )
        if not content.get("include_deleted"):
            payment_query = payment_query.filter(Payment.deleted_by.is_(None))
        payment = payment_query.first()
        if not payment:
            logger.debug("Payment not found")
            return False, None
        payment_dict = payment.to_dict()
        logger.success(f"Payment fetched: {payment_dict}")
        return True, payment_dict
    except Exception as ex:
        logger.exception(f"Error fetching payment: {ex}")
        raise ex


def _get_all_payments(content):
    try:
        logger.debug(f"Fetching all payments: {content}")
        payment = None
        # payment = Payment.query.all()
        payment_query = db.session.query(Payment)
        if not content.get("include_deleted"):
            payment_query = payment_query.filter(Payment.deleted_by.is_(None))
        payment = payment_query.all()
        if not payment:
            logger.debug("No payments found")
            return False, None
        logger.success(f"Payments fetched: {payment}")
        return True, payment
    except Exception as ex:
        logger.exception(f"Error fetching all payments: {ex}")
        raise ex


def _delete_payment(payment):
    try:
        logger.debug(f"Deleting payment: {payment}")
        # Payment.query.filter_by(payment_id=payment.payment_id).delete()
        db.session.query(Payment).filter_by(payment_id=payment.payment_id).delete()
        db.session.commit()
        logger.success(f"Payment deleted: {payment}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting payment: {ex}")
        db.session.rollback()
        return ex


def _add_payment(payment):
    try:
        logger.debug(f"Adding payment: {payment}")
        db.session.add(payment)
        db.session.commit()
        db.session.refresh(payment)
        payment_dict = payment.to_dict()
        logger.success(f"Payment added: {payment_dict}")
        return True, payment
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding payment: {ex}")
        db.session.rollback()
        raise ex


def _update_payment(payment):
    try:
        logger.debug(f"Updating payment: {payment}")
        updated_payment = None
        # Payment.query.filter_by(payment_id=payment.payment_id).update(payment.to_dict())
        updated_payment = db.session.merge(payment)
        db.session.commit()
        if not updated_payment:
            logger.exception("Payment not updated")
            return False, None
        updated_payment_dict = updated_payment.to_dict()
        logger.success(f"Payment updated: {updated_payment_dict}")
        return True, updated_payment_dict
    except Exception as ex:
        logger.exception(f"Error updating payment: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region PaymentProvider Helper Functions
def _get_payment_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching payment by attribute {attribute_name}: {content}")
        payment = None
        payment_query = db.session.query(Payment).filter(
            getattr(Payment, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            payment_query = payment_query.filter(Payment.deleted_by.is_(None))
        payment = payment_query.first()
        if not payment:
            logger.debug(
                f"No payment found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        payment_dict = payment.to_dict()
        logger.success(f"Payment fetched by attribute {attribute_name}: {payment_dict}")
        return True, payment
    except Exception as ex:
        logger.exception(f"Error fetching payment by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_payment_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective payment data by attribute {attribute_name}: {content}"
        )
        payments_dict = None
        payments = (
            db.session.query(Payment)
            .filter(
                getattr(Payment, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            payments_dict = {
                getattr(payment_data, attribute_name): payment_data
                for payment_data in payments
            }
        else:
            payments_dict = {
                getattr(payment_data, attribute_name): payment_data.to_dict()
                for payment_data in payments
            }
        if not payments_dict:
            logger.debug(
                f"No payments found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"Payments fetched by attribute {attribute_name}: {payments_dict}"
        )
        return True, payments_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective payment data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

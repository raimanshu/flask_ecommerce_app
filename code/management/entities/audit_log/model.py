from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    audit_log_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    entity_type = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    entity_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    action = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("user.user_id"), nullable=False)
    # user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    old_data = db.Column(db.JSON, nullable=True)
    new_data = db.Column(db.JSON, nullable=True)
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

    def to_dict(self):
        return {
            "audit_log_id": self.audit_log_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "user_id": self.user_id,
            "old_data": self.old_data,
            "new_data": self.new_data,
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
            logger.debug(f"Adding audit_log: {self} to audit_log table")
            return _add_audit_log(self)
        except Exception as e:
            logger.exception(f"Error adding audit_log: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating audit_log: {self} to audit_log table")
            return _update_audit_log(self)
        except Exception as e:
            logger.exception(f"Error updating audit_log: {e}")
            return False, None

    def delete(audit_log):
        try:
            logger.debug(f"Deleting audit_log: {audit_log} from audit_log table")
            return _delete_audit_log(audit_log)
        except Exception as e:
            logger.exception(f"Error deleting audit_log: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching audit_log: {content} from audit_log table")
            return _get_audit_log(content)
        except Exception as ex:
            logger.exception(f"Error fetching audit_log: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all audit_logs from audit_log table")
            return _get_all_audit_logs(content)
        except Exception as ex:
            logger.exception(f"Error fetching all audit_logs: {ex}")
            return False, None


class AuditLogProvider(AuditLog):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching audit_log by attribute {attribute_name}: {content}")
            return _get_audit_log_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in AuditLogProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_audit_log_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in AuditLogProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region AuditLog Helper Functions


def _get_audit_log(content):
    try:
        logger.debug(f"Fetching audit_log: {content}")
        if content.get("audit_log", ""):
            content["audit_log_id"] = content["audit_log"].audit_log_id
        elif content.get("entity_id", ""):
            content["audit_log_id"] = content["entity_id"]
        audit_log = None
        # audit_log = AuditLog.query.filter_by(audit_log_id=content["audit_log_id"]).first()
        audit_log_query = db.session.query(AuditLog).filter_by(
            audit_log_id=content["audit_log_id"]
        )
        if not content.get("include_deleted"):
            audit_log_query = audit_log_query.filter(AuditLog.deleted_by.is_(None))
        audit_log = audit_log_query.first()
        if not audit_log:
            logger.debug("AuditLog not found")
            return False, None
        audit_log_dict = audit_log.to_dict()
        logger.success(f"AuditLog fetched: {audit_log_dict}")
        return True, audit_log_dict
    except Exception as ex:
        logger.exception(f"Error fetching audit_log: {ex}")
        raise ex


def _get_all_audit_logs(content):
    try:
        logger.debug(f"Fetching all audit_logs: {content}")
        audit_log = None
        # audit_log = AuditLog.query.all()
        audit_log_query = db.session.query(AuditLog)
        if not content.get("include_deleted"):
            audit_log_query = audit_log_query.filter(AuditLog.deleted_by.is_(None))
        audit_log = audit_log_query.all()
        if not audit_log:
            logger.debug("No audit_logs found")
            return False, None
        logger.success(f"AuditLogs fetched: {audit_log}")
        return True, audit_log
    except Exception as ex:
        logger.exception(f"Error fetching all audit_logs: {ex}")
        raise ex


def _delete_audit_log(audit_log):
    try:
        logger.debug(f"Deleting audit_log: {audit_log}")
        # AuditLog.query.filter_by(audit_log_id=audit_log.audit_log_id).delete()
        db.session.query(AuditLog).filter_by(
            audit_log_id=audit_log.audit_log_id
        ).delete()
        db.session.commit()
        logger.success(f"AuditLog deleted: {audit_log}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting audit_log: {ex}")
        db.session.rollback()
        return ex


def _add_audit_log(audit_log):
    try:
        logger.debug(f"Adding audit_log: {audit_log}")
        db.session.add(audit_log)
        db.session.commit()
        db.session.refresh(audit_log)
        audit_log_dict = audit_log.to_dict()
        logger.success(f"AuditLog added: {audit_log_dict}")
        return True, audit_log
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding audit_log: {ex}")
        db.session.rollback()
        raise ex


def _update_audit_log(audit_log):
    try:
        logger.debug(f"Updating audit_log: {audit_log}")
        updated_audit_log = None
        # AuditLog.query.filter_by(audit_log_id=audit_log.audit_log_id).update(audit_log.to_dict())
        updated_audit_log = db.session.merge(audit_log)
        db.session.commit()
        if not updated_audit_log:
            logger.exception("AuditLog not updated")
            return False, None
        updated_audit_log_dict = updated_audit_log.to_dict()
        logger.success(f"AuditLog updated: {updated_audit_log_dict}")
        return True, updated_audit_log_dict
    except Exception as ex:
        logger.exception(f"Error updating audit_log: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region AuditLogProvider Helper Functions
def _get_audit_log_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching audit_log by attribute {attribute_name}: {content}")
        audit_log = None
        audit_log_query = db.session.query(AuditLog).filter(
            getattr(AuditLog, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            audit_log_query = audit_log_query.filter(AuditLog.deleted_by.is_(None))
        audit_log = audit_log_query.first()
        if not audit_log:
            logger.debug(
                f"No audit_log found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        audit_log_dict = audit_log.to_dict()
        logger.success(
            f"AuditLog fetched by attribute {attribute_name}: {audit_log_dict}"
        )
        return True, audit_log
    except Exception as ex:
        logger.exception(
            f"Error fetching audit_log by attribute {attribute_name}: {ex}"
        )
        raise ex


def _get_collective_audit_log_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective audit_log data by attribute {attribute_name}: {content}"
        )
        audit_logs_dict = None
        audit_logs = (
            db.session.query(AuditLog)
            .filter(
                getattr(AuditLog, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            audit_logs_dict = {
                getattr(audit_log_data, attribute_name): audit_log_data
                for audit_log_data in audit_logs
            }
        else:
            audit_logs_dict = {
                getattr(audit_log_data, attribute_name): audit_log_data.to_dict()
                for audit_log_data in audit_logs
            }
        if not audit_logs_dict:
            logger.debug(
                f"No audit_logs found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"AuditLogs fetched by attribute {attribute_name}: {audit_logs_dict}"
        )
        return True, audit_logs_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective audit_log data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

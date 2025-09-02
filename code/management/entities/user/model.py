from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    username = db.Column(db.String(DB_COLUMN_MAX_LENGTH), unique=True, nullable=True)
    name = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    email = db.Column(db.String(DB_COLUMN_MAX_LENGTH), unique=True, nullable=False)
    password = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    contact_number = db.Column(
        db.String(DB_COLUMN_MAX_LENGTH), unique=True, nullable=True
    )
    # address = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
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

    addresses = db.relationship('AddressBook', backref='user', cascade="all, delete-orphan")
    cart = db.relationship('Cart', uselist=False, backref='user')
    orders = db.relationship('Order', backref='user')
    reviews = db.relationship('Review', backref='user')
    audit_logs = db.relationship('AuditLog', backref='user')

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
            "contact_number": self.contact_number,
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
            logger.debug(f"Adding user: {self} to user table")
            return _add_user(self)
        except Exception as e:
            logger.exception(f"Error adding user: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating user: {self} to user table")
            return _update_user(self)
        except Exception as e:
            logger.exception(f"Error updating user: {e}")
            return False, None

    def delete(user):
        try:
            logger.debug(f"Deleting user: {user} from user table")
            return _delete_user(user)
        except Exception as e:
            logger.exception(f"Error deleting user: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching user: {content} from user table")
            return _get_user(content)
        except Exception as ex:
            logger.exception(f"Error fetching user: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all users from user table")
            return _get_all_users(content)
        except Exception as ex:
            logger.exception(f"Error fetching all users: {ex}")
            return False, None


class UserProvider(User):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching user by attribute {attribute_name}: {content}")
            return _get_user_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(f"Critical error in UserProvider.get_by_attribute - {content}")
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_user_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(f"Critical error in UserProvider.get_collective_data_by_attribute - {content}")
            return False, None

# region User Helper Functions

def _get_user(content):
    try:
        logger.debug(f"Fetching user: {content}")
        if content.get("user", ""):
            content["user_id"] = content["user"].user_id
        elif content.get("entity_id", ""):
            content["user_id"] = content["entity_id"]
        user = None
        # user = User.query.filter_by(user_id=content["user_id"]).first()
        user_query = db.session.query(User).filter_by(user_id=content["user_id"])
        if not content.get("include_deleted"):
            user_query = user_query.filter(User.deleted_by.is_(None))
        user = user_query.first()
        if not user:
            logger.debug("User not found")
            return False, None
        user_dict = user.to_dict()
        logger.success(f"User fetched: {user_dict}")
        return True, user_dict
    except Exception as ex:
        logger.exception(f"Error fetching user: {ex}")
        raise ex
    

def _get_all_users(content):
    try:
        logger.debug(f"Fetching all users: {content}")
        user = None
        # user = User.query.all()
        user_query = db.session.query(User)
        if not content.get("include_deleted"):
            user_query = user_query.filter(User.deleted_by.is_(None))
        user = user_query.all()
        if not user:
            logger.debug("No users found")
            return False, None
        logger.success(f"Users fetched: {user}")
        return True, user
    except Exception as ex:
        logger.exception(f"Error fetching all users: {ex}")
        raise ex
    
def _delete_user(user):
    try:
        logger.debug(f"Deleting user: {user}")
        # User.query.filter_by(user_id=user.user_id).delete()
        db.session.query(User).filter_by(user_id=user.user_id).delete()
        db.session.commit()
        logger.success(f"User deleted: {user}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting user: {ex}")
        db.session.rollback()
        return ex

def _add_user(user):
    try:
        logger.debug(f"Adding user: {user}")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        user_dict = user.to_dict()
        logger.success(f"User added: {user_dict}")
        return True, user
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding user: {ex}")
        db.session.rollback()
        raise ex


def _update_user(user):
    try:
        logger.debug(f"Updating user: {user}")      
        updated_user = None
        # User.query.filter_by(user_id=user.user_id).update(user.to_dict())
        updated_user = db.session.merge(user)
        db.session.commit()
        if not updated_user:
            logger.exception("User not updated")
            return False, None
        updated_user_dict = updated_user.to_dict()
        logger.success(f"User updated: {updated_user_dict}")
        return True, updated_user_dict
    except Exception as ex:
        logger.exception(f"Error updating user: {ex}")
        db.session.rollback()
        raise ex

# endregion 

# region UserProvider Helper Functions
def _get_user_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching user by attribute {attribute_name}: {content}")
        user = None
        user_query = (
            db.session
            .query(User)
            .filter(
                getattr(User, attribute_name) == content.get(f"{attribute_name}", "")
            )
        )
        if not content.get("include_deleted", False):
            user_query = user_query.filter(User.deleted_by.is_(None))
        user = user_query.first()
        if not user:
            logger.debug(f"No user found with {attribute_name} in {content.get(f'{attribute_name}', '')}")
            return False, None
        user_dict = user.to_dict()
        logger.success(f"User fetched by attribute {attribute_name}: {user_dict}")
        return True, user
    except Exception as ex:
        logger.exception(f"Error fetching user by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_user_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective user data by attribute {attribute_name}: {content}"
        )
        users_dict = None
        users = (
            db.session
            .query(User)
            .filter(
                getattr(User, attribute_name).in_(content.get(f"{attribute_name}", []))
            )
            .all()
        )
        if require_object:
            users_dict = {
                getattr(user_data, attribute_name): user_data for user_data in users
            }
        else:
            users_dict = {
                getattr(user_data, attribute_name): user_data.to_dict()
                for user_data in users
            }
        if not users_dict:
            logger.debug(f"No users found with {attribute_name} in {content.get(f'{attribute_name}', '')}")
            return False, None
        logger.success(f"Users fetched by attribute {attribute_name}: {users_dict}")
        return True, users_dict
    except Exception as ex:
        logger.exception(f"Error fetching collective user data by attribute {attribute_name}: {ex}")
        raise ex


# endregion
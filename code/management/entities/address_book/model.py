from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class AddressBook(db.Model):
    __tablename__ = "address_book"

    address_book_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("user.user_id"), nullable=False)
    # user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    address_line1 = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    address_line2 = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    city = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    state = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    country = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    zip_code = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
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
            "address_book_id": self.address_book_id,
            "user_id": self.user_id,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "zip_code": self.zip_code,
            "is_default": self.is_default,
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
            logger.debug(f"Adding address_book: {self} to address_book table")
            return _add_address_book(self)
        except Exception as e:
            logger.exception(f"Error adding address_book: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating address_book: {self} to address_book table")
            return _update_address_book(self)
        except Exception as e:
            logger.exception(f"Error updating address_book: {e}")
            return False, None

    def delete(address_book):
        try:
            logger.debug(
                f"Deleting address_book: {address_book} from address_book table"
            )
            return _delete_address_book(address_book)
        except Exception as e:
            logger.exception(f"Error deleting address_book: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching address_book: {content} from address_book table")
            return _get_address_book(content)
        except Exception as ex:
            logger.exception(f"Error fetching address_book: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all address_books from address_book table")
            return _get_all_address_books(content)
        except Exception as ex:
            logger.exception(f"Error fetching all address_books: {ex}")
            return False, None


class AddressBookProvider(AddressBook):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(
                f"Fetching address_book by attribute {attribute_name}: {content}"
            )
            return _get_address_book_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in AddressProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_address_book_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in AddressBookProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region AddressBook Helper Functions


def _get_address_book(content):
    try:
        logger.debug(f"Fetching address_book: {content}")
        if content.get("address_book", ""):
            content["address_book_id"] = content["address_book"].address_book_id
        elif content.get("entity_id", ""):
            content["address_book_id"] = content["entity_id"]
        address_book = None
        # address_book = AddressBook.query.filter_by(address_book_id=content["address_book_id"]).first()
        address_book_query = db.session.query(AddressBook).filter_by(
            address_book_id=content["address_book_id"]
        )
        if not content.get("include_deleted"):
            address_book_query = address_book_query.filter(
                AddressBook.deleted_by.is_(None)
            )
        address_book = address_book_query.first()
        if not address_book:
            logger.debug("AddressBook not found")
            return False, None
        address_book_dict = address_book.to_dict()
        logger.success(f"AddressBook fetched: {address_book_dict}")
        return True, address_book_dict
    except Exception as ex:
        logger.exception(f"Error fetching address_book: {ex}")
        raise ex


def _get_all_address_books(content):
    try:
        logger.debug(f"Fetching all address_books: {content}")
        address_book = None
        # address_book = AddressBook.query.all()
        address_book_query = db.session.query(AddressBook)
        if not content.get("include_deleted"):
            address_book_query = address_book_query.filter(
                AddressBook.deleted_by.is_(None)
            )
        address_book = address_book_query.all()
        if not address_book:
            logger.debug("No address_books found")
            return False, None
        logger.success(f"AddressBooks fetched: {address_book}")
        return True, address_book
    except Exception as ex:
        logger.exception(f"Error fetching all address_books: {ex}")
        raise ex


def _delete_address_book(address_book):
    try:
        logger.debug(f"Deleting address_book: {address_book}")
        # AddressBook.query.filter_by(address_book_id=address_book.address_book_id).delete()
        db.session.query(AddressBook).filter_by(
            address_book_id=address_book.address_book_id
        ).delete()
        db.session.commit()
        logger.success(f"AddressBook deleted: {address_book}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting address_book: {ex}")
        db.session.rollback()
        return ex


def _add_address_book(address_book):
    try:
        logger.debug(f"Adding address_book: {address_book}")
        db.session.add(address_book)
        db.session.commit()
        db.session.refresh(address_book)
        address_book_dict = address_book.to_dict()
        logger.success(f"AddressBook added: {address_book_dict}")
        return True, address_book
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding address_book: {ex}")
        db.session.rollback()
        raise ex


def _update_address_book(address_book):
    try:
        logger.debug(f"Updating address_book: {address_book}")
        updated_address_book = None
        # AddressBook.query.filter_by(address_book_id=address_book.address_book_id).update(address_book.to_dict())
        updated_address_book = db.session.merge(address_book)
        db.session.commit()
        if not updated_address_book:
            logger.exception("AddressBook not updated")
            return False, None
        updated_address_book_dict = updated_address_book.to_dict()
        logger.success(f"AddressBook updated: {updated_address_book_dict}")
        return True, updated_address_book_dict
    except Exception as ex:
        logger.exception(f"Error updating address_book: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region AddressBookProvider Helper Functions
def _get_address_book_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching address_book by attribute {attribute_name}: {content}")
        address_book = None
        address_book_query = db.session.query(AddressBook).filter(
            getattr(AddressBook, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            address_book_query = address_book_query.filter(
                AddressBook.deleted_by.is_(None)
            )
        address_book = address_book_query.first()
        if not address_book:
            logger.debug(
                f"No address_book found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        address_book_dict = address_book.to_dict()
        logger.success(
            f"AddressBook fetched by attribute {attribute_name}: {address_book_dict}"
        )
        return True, address_book
    except Exception as ex:
        logger.exception(
            f"Error fetching address_book by attribute {attribute_name}: {ex}"
        )
        raise ex


def _get_collective_address_book_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective address_book data by attribute {attribute_name}: {content}"
        )
        address_books_dict = None
        address_books = (
            db.session.query(AddressBook)
            .filter(
                getattr(AddressBook, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            address_books_dict = {
                getattr(address_book_data, attribute_name): address_book_data
                for address_book_data in address_books
            }
        else:
            address_books_dict = {
                getattr(address_book_data, attribute_name): address_book_data.to_dict()
                for address_book_data in address_books
            }
        if not address_books_dict:
            logger.debug(
                f"No address_books found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"AddressBooks fetched by attribute {attribute_name}: {address_books_dict}"
        )
        return True, address_books_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective address_book data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class ProductInventory(db.Model):
    __tablename__ = "product_inventory"

    product_inventory_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("product.product_id"), nullable=False)
    # product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    reserved_quantity = db.Column(db.Integer, default=0)
    warehouse_location = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    attributes = db.Column(db.JSON, default={})
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
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
            "product_inventory_id": self.product_inventory_id,
            "product_id": self.product_id,
            "stock_quantity": self.stock_quantity,
            "reserved_quantity": self.reserved_quantity,
            "warehouse_location": self.warehouse_location,
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
            logger.debug(f"Adding product_inventory: {self} to product_inventory table")
            return _add_product_inventory(self)
        except Exception as e:
            logger.exception(f"Error adding product_inventory: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(
                f"Updating product_inventory: {self} to product_inventory table"
            )
            return _update_product_inventory(self)
        except Exception as e:
            logger.exception(f"Error updating product_inventory: {e}")
            return False, None

    def delete(product_inventory):
        try:
            logger.debug(
                f"Deleting product_inventory: {product_inventory} from product_inventory table"
            )
            return _delete_product_inventory(product_inventory)
        except Exception as e:
            logger.exception(f"Error deleting product_inventory: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(
                f"Fetching product_inventory: {content} from product_inventory table"
            )
            return _get_product_inventory(content)
        except Exception as ex:
            logger.exception(f"Error fetching product_inventory: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(
                f"Fetching all product_inventorys from product_inventory table"
            )
            return _get_all_product_inventorys(content)
        except Exception as ex:
            logger.exception(f"Error fetching all product_inventorys: {ex}")
            return False, None


class ProductInventoryProvider(ProductInventory):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(
                f"Fetching product_inventory by attribute {attribute_name}: {content}"
            )
            return _get_product_inventory_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in ProductInventoryProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_product_inventory_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in ProductInventoryProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region ProductInventory Helper Functions


def _get_product_inventory(content):
    try:
        logger.debug(f"Fetching product_inventory: {content}")
        if content.get("product_inventory", ""):
            content["product_inventory_id"] = content[
                "product_inventory"
            ].product_inventory_id
        elif content.get("entity_id", ""):
            content["product_inventory_id"] = content["entity_id"]
        product_inventory = None
        # product_inventory = ProductInventory.query.filter_by(product_inventory_id=content["product_inventory_id"]).first()
        product_inventory_query = db.session.query(ProductInventory).filter_by(
            product_inventory_id=content["product_inventory_id"]
        )
        if not content.get("include_deleted"):
            product_inventory_query = product_inventory_query.filter(
                ProductInventory.deleted_by.is_(None)
            )
        product_inventory = product_inventory_query.first()
        if not product_inventory:
            logger.debug("ProductInventory not found")
            return False, None
        product_inventory_dict = product_inventory.to_dict()
        logger.success(f"ProductInventory fetched: {product_inventory_dict}")
        return True, product_inventory_dict
    except Exception as ex:
        logger.exception(f"Error fetching product_inventory: {ex}")
        raise ex


def _get_all_product_inventorys(content):
    try:
        logger.debug(f"Fetching all product_inventorys: {content}")
        product_inventory = None
        # product_inventory = ProductInventory.query.all()
        product_inventory_query = db.session.query(ProductInventory)
        if not content.get("include_deleted"):
            product_inventory_query = product_inventory_query.filter(
                ProductInventory.deleted_by.is_(None)
            )
        product_inventory = product_inventory_query.all()
        if not product_inventory:
            logger.debug("No product_inventorys found")
            return False, None
        logger.success(f"ProductInventorys fetched: {product_inventory}")
        return True, product_inventory
    except Exception as ex:
        logger.exception(f"Error fetching all product_inventorys: {ex}")
        raise ex


def _delete_product_inventory(product_inventory):
    try:
        logger.debug(f"Deleting product_inventory: {product_inventory}")
        # ProductInventory.query.filter_by(product_inventory_id=product_inventory.product_inventory_id).delete()
        db.session.query(ProductInventory).filter_by(
            product_inventory_id=product_inventory.product_inventory_id
        ).delete()
        db.session.commit()
        logger.success(f"ProductInventory deleted: {product_inventory}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting product_inventory: {ex}")
        db.session.rollback()
        return ex


def _add_product_inventory(product_inventory):
    try:
        logger.debug(f"Adding product_inventory: {product_inventory}")
        db.session.add(product_inventory)
        db.session.commit()
        db.session.refresh(product_inventory)
        product_inventory_dict = product_inventory.to_dict()
        logger.success(f"ProductInventory added: {product_inventory_dict}")
        return True, product_inventory
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding product_inventory: {ex}")
        db.session.rollback()
        raise ex


def _update_product_inventory(product_inventory):
    try:
        logger.debug(f"Updating product_inventory: {product_inventory}")
        updated_product_inventory = None
        # ProductInventory.query.filter_by(product_inventory_id=product_inventory.product_inventory_id).update(product_inventory.to_dict())
        updated_product_inventory = db.session.merge(product_inventory)
        db.session.commit()
        if not updated_product_inventory:
            logger.exception("ProductInventory not updated")
            return False, None
        updated_product_inventory_dict = updated_product_inventory.to_dict()
        logger.success(f"ProductInventory updated: {updated_product_inventory_dict}")
        return True, updated_product_inventory_dict
    except Exception as ex:
        logger.exception(f"Error updating product_inventory: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region ProductInventoryProvider Helper Functions
def _get_product_inventory_by_attribute(attribute_name, content):
    try:
        logger.debug(
            f"Fetching product_inventory by attribute {attribute_name}: {content}"
        )
        product_inventory = None
        product_inventory_query = db.session.query(ProductInventory).filter(
            getattr(ProductInventory, attribute_name)
            == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            product_inventory_query = product_inventory_query.filter(
                ProductInventory.deleted_by.is_(None)
            )
        product_inventory = product_inventory_query.first()
        if not product_inventory:
            logger.debug(
                f"No product_inventory found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        product_inventory_dict = product_inventory.to_dict()
        logger.success(
            f"ProductInventory fetched by attribute {attribute_name}: {product_inventory_dict}"
        )
        return True, product_inventory
    except Exception as ex:
        logger.exception(
            f"Error fetching product_inventory by attribute {attribute_name}: {ex}"
        )
        raise ex


def _get_collective_product_inventory_by_attribute(
    attribute_name, content, require_object
):
    try:
        logger.debug(
            f"Fetching collective product_inventory data by attribute {attribute_name}: {content}"
        )
        product_inventorys_dict = None
        product_inventorys = (
            db.session.query(ProductInventory)
            .filter(
                getattr(ProductInventory, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            product_inventorys_dict = {
                getattr(product_inventory_data, attribute_name): product_inventory_data
                for product_inventory_data in product_inventorys
            }
        else:
            product_inventorys_dict = {
                getattr(
                    product_inventory_data, attribute_name
                ): product_inventory_data.to_dict()
                for product_inventory_data in product_inventorys
            }
        if not product_inventorys_dict:
            logger.debug(
                f"No product_inventorys found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(
            f"ProductInventorys fetched by attribute {attribute_name}: {product_inventorys_dict}"
        )
        return True, product_inventorys_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective product_inventory data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

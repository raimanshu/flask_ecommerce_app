from infra.database import db
from utils.constants import DB_COLUMN_MAX_LENGTH


class Product(db.Model):
    __tablename__ = "products"

    product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    name = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    brand = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    category = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    attributes = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    modified_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    modified_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)



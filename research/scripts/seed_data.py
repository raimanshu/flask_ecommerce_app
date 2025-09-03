import os
import json
import uuid
import sys
import bcrypt
from pathlib import Path

from flask import Flask
from dotenv import load_dotenv

# Setup code path
code_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "code"))
sys.path.append(code_path)

# Import shared db and models
from infra.database import db
from infra.environment import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from management.entities.user.model import User
from management.entities.product.model import Product
from management.entities.order.model import Order
from management.entities.order_item.model import OrderItem
from management.entities.address_book.model import AddressBook
from management.entities.category.model import Category
from management.entities.brand.model import Brand
from management.entities.product_inventory.model import ProductInventory
from management.entities.product_image.model import ProductImage
from management.entities.cart.model import Cart
from management.entities.cart_item.model import CartItem
from management.entities.payment.model import Payment
from management.entities.shipping.model import Shipping
from management.entities.coupon.model import Coupon
from management.entities.review.model import Review
from management.entities.audit_log.model import AuditLog

from utils.utility import get_current_time, string_to_base64

load_dotenv()

# Ensure database folder exists (place this right here)
db_path = Path(SQLALCHEMY_DATABASE_URI.replace("sqlite:///", ""))
db_path.parent.mkdir(parents=True, exist_ok=True)

# Initialize app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS

db.init_app(app)

# Load JSON data
DATA_FILE = Path(__file__).parent.parent / "data" / "seed_data_2.json"


# def seed_users(users_data):
#     for entry in users_data:
#         if User.query.filter_by(email=entry["email"]).first():
#             print(f"User {entry['email']} exists. Skipping.")
#             continue
#         user = User(
#             user_id=str(uuid.uuid4()),
#             username=entry["username"],
#             name=entry["name"],
#             email=entry["email"],
#             password=entry["password"],
#             contact_number=entry.get("contact_number"),
#             address=entry.get("address"),
#             attributes=entry.get("attributes", {}),
#             created_at=get_current_time(),
#             created_by=entry["created_by"],
#             modified_by=entry["created_by"],
#         )
#         db.session.add(user)
#     print("✅ Users seeded.")


# def seed_products(products_data):
#     for entry in products_data:
#         if Product.query.filter_by(name=entry["name"], brand=entry["brand"]).first():
#             print(f"Product {entry['name']} by {entry['brand']} exists. Skipping.")
#             continue
#         product = Product(
#             product_id=str(uuid.uuid4()),
#             name=entry["name"],
#             description=entry.get("description"),
#             price=entry["price"],
#             brand=entry["brand"],
#             category=entry["category"],
#             attributes=entry.get("attributes", {}),
#             stock_quantity=entry.get("stock_quantity", 0),
#             created_by=entry["created_by"],
#             modified_by=entry["created_by"],
#         )
#         db.session.add(product)
#     print("✅ Products seeded.")


# def seed_all():
#     with app.app_context():
#         db.create_all()
#         with open(DATA_FILE, "r") as f:
#             data = json.load(f)
#         if "users" in data:
#             seed_users(data["users"])
#         if "products" in data:
#             seed_products(data["products"])
#         db.session.commit()
#         print("🎉 Seeding complete.")


def seed_all():
    with app.app_context():
        db.create_all()
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        # # Seed users first
        # user_ids = seed_users(data.get("users", []))
        # # Seed products
        # product_ids = seed_products(data.get("products", []))
        # # Seed orders
        # order_ids = seed_orders(data.get("orders", []), user_ids)
        # # Seed order items
        # seed_order_items(data.get("order_items", []), order_ids, product_ids)

        # user_ids = seed_users(data.get("users", []))
        # product_ids = seed_products(data.get("products", []))

        # address_book_ids = seed_address_books(data.get("address_books", []))
        # category_ids = seed_categories(data.get("categories", []))
        # product_inventory_ids = seed_product_inventories(data.get("product_inventories", []))
        # product_image_ids = seed_product_images(data.get("product_images", []))
        # cart_ids = seed_carts(data.get("carts", []))
        # cart_item_ids = seed_cart_items(data.get("cart_items", []))
        # order_ids = seed_orders(data.get("orders", []))
        # order_item_ids = seed_order_items(data.get("order_items", []))
        # payment_ids = seed_payments(data.get("payments", []))
        # shipping_ids = seed_shippings(data.get("shippings", []))
        # coupon_ids = seed_coupons(data.get("coupons", []))
        # review_ids = seed_reviews(data.get("reviews", []))
        # audit_log_ids = seed_audit_logs(data.get("audit_logs", []))
        # brand_ids = seed_brands(data.get("brands", []))

        table_name_list = {
            "user": [
                "user_id",
                "username",
                "password",
                "name",
                "email",
                "contact_number",
                "is_active",
                "is_verified",
                "attributes",
                "created_by",
                "created_at",
            ],
            "address_book": [
                "address_book_id",
                "user_id",
                "address_line1",
                "address_line2",
                "city",
                "state",
                "country",
                "zip_code",
                "is_default",
                "attributes",
                # "created_at",
                "created_by",
            ],
            "category": [
                "category_id",
                "name",
                "slug",
                "parent_category_id",
                "description",
                "attributes",
                # "created_at",
                "created_by",
            ],
            "brand": ["brand_id", "name", "description", "attributes", "created_by"],
            "product": [
                "product_id",
                "name",
                "slug",
                "description",
                "brand_id",
                "category_id",
                "price",
                "discount_price",
                "sku",
                "is_active",
                "attributes",
                "created_by",
            ],
            "product_inventory": [
                "product_inventory_id",
                "product_id",
                "stock_quantity",
                "reserved_quantity",
                "warehouse_location",
                "attributes",
                "created_by",
            ],
            "product_image": [
                "product_image_id",
                "product_id",
                "image_url",
                "alt_text",
                "is_main",
                "attributes",
                "created_by",
            ],
            "cart": ["cart_id", "user_id", "attributes", "created_by"],
            "cart_item": [
                "cart_item_id",
                "cart_id",
                "product_id",
                "quantity",
                "attributes",
                "created_by",
            ],
            "order": [
                "order_id",
                "user_id",
                "order_number",
                "total_amount",
                "shipping_fee",
                "discount_amount",
                "payment_status",
                "order_status",
                "shipping_address_id",
                "attributes",
                "created_by",
            ],
            "order_item": [
                "order_item_id",
                "order_id",
                "product_id",
                "quantity",
                "unit_price",
                "total_price",
                "attributes",
                "created_by",
            ],
            "payment": [
                "payment_id",
                "order_id",
                "payment_method",
                "payment_reference",
                "amount",
                "status",
                "paid_at",
                "attributes",
                "created_by",
            ],
            "shipping": [
                "shipping_id",
                "order_id",
                "courier_name",
                "tracking_number",
                "status",
                "shipped_at",
                "delivered_at",
                "attributes",
                "created_by",
            ],
            "coupon": [
                "coupon_id",
                "code",
                "discount_value",
                "min_order_value",
                "max_discount",
                "valid_from",
                "valid_to",
                "is_active",
                "usage_limit",
                "usage_count",
                "attributes",
                "created_by",
            ],
            "review": [
                "review_id",
                "user_id",
                "product_id",
                "rating",
                "comment",
                "attributes",
                "created_by",
            ],
            "audit_log": [
                "audit_log_id",
                "entity_type",
                "entity_id",
                "action",
                "user_id",
                "old_data",
                "new_data",
                "attributes",
                "created_by",
            ],
        }

        no_params_tables = ["user", "category", "coupon", "brand", "product"]
        single_params_tables = [
            "address_book",
            "order",
            "cart",
            "audit_log",
            "payment",
            "shipping",
            "product_inventory",
            "product_image",
        ]
        double_params_tables = ["cart_item", "order_item", "review"]

        for table_name, table_columns_list in table_name_list.items():
            if table_name in no_params_tables:
                seed_all_data(
                    table_name,
                    table_columns_list,
                    data.get(table_name),
                    to_pascal_case(table_name),
                )

        for table_name, table_columns_list in table_name_list.items():
            if table_name in single_params_tables:
                seed_all_data(
                    table_name,
                    table_columns_list,
                    data.get(table_name),
                    to_pascal_case(table_name),
                )

        for table_name, table_columns_list in table_name_list.items():
            if table_name in double_params_tables:
                seed_all_data(
                    table_name,
                    table_columns_list,
                    data.get(table_name),
                    to_pascal_case(table_name),
                )

        db.session.commit()
        print("🎉 Seeding complete.")


def to_pascal_case(snake_str):
    parts = snake_str.strip("_").split("_")
    return "".join(word.capitalize() for word in parts if word)


def seed_all_data(table_name, table_column_list, data_rows, table_class_name):
    table_class = globals().get(table_class_name)
    if table_class is None:
        raise ValueError(f"Class '{table_class_name}' not found in globals()")

    for row in data_rows:  # Loop through each record (dict)
        payload = {}
        payload["created_at"] = get_current_time()
        print(f"===============================================   {table_column_list}")
        for column in table_column_list:
            if column == "attributes":
                payload["attributes"] = row.get("attributes", {})
            if column == "password":
                payload["password"] = string_to_base64(row.get("password", ""))
                # payload["password"] = bcrypt.hashpw(row.get("password", ""), bcrypt.gensalt())
            elif column in [
                "paid_at",
                "shipped_at",
                "valid_from",
                "valid_to",
                "delivered_at",
                "created_at",
            ]:
                payload[column] = get_current_time()
            else:
                payload[column] = row.get(column)

        print(f"Seeding: {payload}")
        obj = table_class(**payload)
        db.session.add(obj)

    db.session.commit()


if __name__ == "__main__":
    seed_all()

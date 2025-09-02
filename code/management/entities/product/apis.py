from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.product.model import Product
from utils.utility import (
    generate_bad_request_response,
    generate_entity_not_found_response,
    generate_internal_server_error_response,
    generate_not_acceptable_response,
    generate_success_response,
    generate_service_unavailable_error_response,
    extract_query_params,
    get_current_time
)
from sqlalchemy import String, cast, desc, or_
from sqlalchemy.inspection import inspect
from infra.logging import logger


def create_product(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating product with content: {content}")
        if "product" not in content:
            response = generate_bad_request_response(
                "Product data is required to create a product."
            )
            return response
        product = Product(**content["product"].model_dump())
        status, product_data = Product.add(product)
        if not status:
            response = generate_not_acceptable_response("Product creation failed.")
            return response
        response = generate_success_response("product created successfully")
        logger.success(f"Product created: {product_data}")
        response["product"] = product_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_product: {ex}")
    return response


def get_product(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching product with content: {content}")
        if "product_id" not in content:
            response = generate_bad_request_response(
                "Product ID is required to fetch product details."
            )
            return response
        status, product = Product.get(content)
        if not status:
            response = generate_entity_not_found_response("Product")
            return response
        logger.success(f"Product fetched: {product}")
        response = generate_success_response("product fetched successfully")
        response["product"] = product
    except Exception as ex:
        logger.exception(f"Error in get_product: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_products(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all products with content: {content}")
        product_data, all_product_data = [], []
        _, all_product_data = Product.get_all(content)
        if not all_product_data:
            response = generate_entity_not_found_response("Products")
            return response
        for product in all_product_data:
            product_data.append(product.to_dict())
        logger.success(f"Products fetched: {product_data}")
        response = generate_success_response("All products fetched successfully")
        response["product"] = product_data
    except Exception as ex:
        logger.exception(f"Error in get_all_products: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_product(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating product with content: {content}")
        updated_product = None
        content["product_id"] = content["product"].product_id
        status, product_data = Product.get(content)
        if not status:
            response = generate_entity_not_found_response("Product")
            return response
        product_data = Product(**product_data)
        incoming_data = content["product"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                product_data.attributes = {**product_data.attributes, **value}
            else:
                setattr(product_data, key, value)
        product_data.modified_at = content["product"].modified_at
        status, updated_product = Product.update(product_data)
        if not status:
            response = generate_not_acceptable_response("Product update failed.")
            return response
        logger.success(f"Product updated: {updated_product}")
        response = generate_success_response("product updated successfully")
        response["product"] = updated_product
    except Exception as ex:
        logger.exception(f"Error in update_product: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_product(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting product with content: {content}")
        if "product_id" not in content:
            response = generate_bad_request_response(
                "Product ID is required to delete product."
            )
            return response
        status, product = Product.get(content)
        if not status:
            response = generate_entity_not_found_response("Product")
            return response
        product_data = Product(**product)

        # for hard delete
        # status = Product.delete(product_data)

        # for soft delete
        if "product" in content:
            product.deleted_by = content["product"].deleted_by
            product.deleted_at = content["product"].deleted_at
        elif "current_product" in content:
            product.deleted_by = content["current_product"].product_id
            product.deleted_at = get_current_time()
            status, _ = Product.update(product_data)
        if not status:
            response = generate_not_acceptable_response("Product deletion failed.")
            return response
        logger.success(f"Product deleted: {product}")
        response = generate_success_response("product deleted successfully")
        response["product"] = product
    except Exception as ex:
        logger.exception(f"Error in delete_product: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_products(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total products with content: {content}")
        total_products, search_criteria = 0, []
        product_query = Product.query
        columns = inspect(Product).columns

        if not content.get("include_deleted"):
            product_query = product_query.filter(Product.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Product, content["selected_column"], None)
                if selected_column:
                    search_criteria.append(
                        cast(selected_column, String).ilike(
                            f"%{content['search_string']}%"
                        )
                    )
            else:
                for column in columns:
                    search_criteria.append(
                        cast(column, String).ilike(f"%{search_string}%")
                    )
        product_query = product_query.filter(or_(*search_criteria))
        total_products = product_query.count()
        logger.success(f"Total products fetched: {total_products}")
        response = generate_success_response("Total products fetched successfully")
        response["total_products"] = total_products
    except Exception as ex:
        logger.exception(f"Error in get_total_products: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_products(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited products with content: {content}")
        products_data, products, columns_list = [], None, None
        product_query = Product.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Product).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            product_query = product_query.filter(Product.deleted_by.is_(None))
        products = (
            product_query.order_by(desc(Product.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for product in products:
            products_data.append(product.to_dict())
        logger.success(f"Products fetched: {products_data}")
        response = generate_success_response("Limited products fetched successfully")
        response["records"] = products_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_products: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_products(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered products with content: {content}")
        products_data, products, columns_list, search_criteria = [], [], None, []
        product_query = Product.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Product).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Product, content["selected_column"], None)
                if selected_column:
                    search_criteria.append(
                        cast(selected_column, String).ilike(
                            f"%{content['search_string']}%"
                        )
                    )
            else:
                for column in columns:
                    search_criteria.append(
                        cast(column, String).ilike(f"%{search_string}%")
                    )
        product_query = product_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            product_query = product_query.filter(Product.deleted_by.is_(None))
        products = (
            product_query.order_by(desc(Product.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for product in products:
            products_data.append(product.to_dict())

        logger.success(f"Products fetched: {products_data}")
        response = generate_success_response("Filtered products fetched successfully")
        response["records"] = products_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_products: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

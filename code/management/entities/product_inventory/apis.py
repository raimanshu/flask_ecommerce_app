from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.product_inventory.model import ProductInventory
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


def create_product_inventory(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating product_inventory with content: {content}")
        if "product_inventory" not in content:
            response = generate_bad_request_response(
                "ProductInventory data is required to create a product_inventory."
            )
            return response
        product_inventory = ProductInventory(**content["product_inventory"].model_dump())
        status, product_inventory_data = ProductInventory.add(product_inventory)
        if not status:
            response = generate_not_acceptable_response("ProductInventory creation failed.")
            return response
        response = generate_success_response("product_inventory created successfully")
        logger.success(f"ProductInventory created: {product_inventory_data}")
        response["product_inventory"] = product_inventory_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_product_inventory: {ex}")
    return response


def get_product_inventory(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching product_inventory with content: {content}")
        if "product_inventory_id" not in content:
            response = generate_bad_request_response(
                "ProductInventory ID is required to fetch product_inventory details."
            )
            return response
        status, product_inventory = ProductInventory.get(content)
        if not status:
            response = generate_entity_not_found_response("ProductInventory")
            return response
        logger.success(f"ProductInventory fetched: {product_inventory}")
        response = generate_success_response("product_inventory fetched successfully")
        response["product_inventory"] = product_inventory
    except Exception as ex:
        logger.exception(f"Error in get_product_inventory: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_product_inventorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all product_inventorys with content: {content}")
        product_inventory_data, all_product_inventory_data = [], []
        _, all_product_inventory_data = ProductInventory.get_all(content)
        if not all_product_inventory_data:
            response = generate_entity_not_found_response("ProductInventorys")
            return response
        for product_inventory in all_product_inventory_data:
            product_inventory_data.append(product_inventory.to_dict())
        logger.success(f"ProductInventorys fetched: {product_inventory_data}")
        response = generate_success_response("All product_inventorys fetched successfully")
        response["product_inventory"] = product_inventory_data
    except Exception as ex:
        logger.exception(f"Error in get_all_product_inventorys: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_product_inventory(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating product_inventory with content: {content}")
        updated_product_inventory = None
        content["product_inventory_id"] = content["product_inventory"].product_inventory_id
        status, product_inventory_data = ProductInventory.get(content)
        if not status:
            response = generate_entity_not_found_response("ProductInventory")
            return response
        product_inventory_data = ProductInventory(**product_inventory_data)
        incoming_data = content["product_inventory"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                product_inventory_data.attributes = {**product_inventory_data.attributes, **value}
            else:
                setattr(product_inventory_data, key, value)
        product_inventory_data.modified_at = content["product_inventory"].modified_at
        status, updated_product_inventory = ProductInventory.update(product_inventory_data)
        if not status:
            response = generate_not_acceptable_response("ProductInventory update failed.")
            return response
        logger.success(f"ProductInventory updated: {updated_product_inventory}")
        response = generate_success_response("product_inventory updated successfully")
        response["product_inventory"] = updated_product_inventory
    except Exception as ex:
        logger.exception(f"Error in update_product_inventory: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_product_inventory(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting product_inventory with content: {content}")
        if "product_inventory_id" not in content:
            response = generate_bad_request_response(
                "ProductInventory ID is required to delete product_inventory."
            )
            return response
        status, product_inventory = ProductInventory.get(content)
        if not status:
            response = generate_entity_not_found_response("ProductInventory")
            return response
        product_inventory_data = ProductInventory(**product_inventory)

        # for hard delete
        # status = ProductInventory.delete(product_inventory_data)

        # for soft delete
        if "product_inventory" in content:
            product_inventory.deleted_by = content["product_inventory"].deleted_by
            product_inventory.deleted_at = content["product_inventory"].deleted_at
        elif "current_product_inventory" in content:
            product_inventory.deleted_by = content["current_product_inventory"].product_inventory_id
            product_inventory.deleted_at = get_current_time()
            status, _ = ProductInventory.update(product_inventory_data)
        if not status:
            response = generate_not_acceptable_response("ProductInventory deletion failed.")
            return response
        logger.success(f"ProductInventory deleted: {product_inventory}")
        response = generate_success_response("product_inventory deleted successfully")
        response["product_inventory"] = product_inventory
    except Exception as ex:
        logger.exception(f"Error in delete_product_inventory: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_product_inventorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total product_inventorys with content: {content}")
        total_product_inventorys, search_criteria = 0, []
        product_inventory_query = ProductInventory.query
        columns = inspect(ProductInventory).columns

        if not content.get("include_deleted"):
            product_inventory_query = product_inventory_query.filter(ProductInventory.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(ProductInventory, content["selected_column"], None)
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
        product_inventory_query = product_inventory_query.filter(or_(*search_criteria))
        total_product_inventorys = product_inventory_query.count()
        logger.success(f"Total product_inventorys fetched: {total_product_inventorys}")
        response = generate_success_response("Total product_inventorys fetched successfully")
        response["total_product_inventorys"] = total_product_inventorys
    except Exception as ex:
        logger.exception(f"Error in get_total_product_inventorys: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_product_inventorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited product_inventorys with content: {content}")
        product_inventorys_data, product_inventorys, columns_list = [], None, None
        product_inventory_query = ProductInventory.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(ProductInventory).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            product_inventory_query = product_inventory_query.filter(ProductInventory.deleted_by.is_(None))
        product_inventorys = (
            product_inventory_query.order_by(desc(ProductInventory.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for product_inventory in product_inventorys:
            product_inventorys_data.append(product_inventory.to_dict())
        logger.success(f"ProductInventorys fetched: {product_inventorys_data}")
        response = generate_success_response("Limited product_inventorys fetched successfully")
        response["records"] = product_inventorys_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_product_inventorys: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_product_inventorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered product_inventorys with content: {content}")
        product_inventorys_data, product_inventorys, columns_list, search_criteria = [], [], None, []
        product_inventory_query = ProductInventory.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(ProductInventory).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(ProductInventory, content["selected_column"], None)
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
        product_inventory_query = product_inventory_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            product_inventory_query = product_inventory_query.filter(ProductInventory.deleted_by.is_(None))
        product_inventorys = (
            product_inventory_query.order_by(desc(ProductInventory.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for product_inventory in product_inventorys:
            product_inventorys_data.append(product_inventory.to_dict())

        logger.success(f"ProductInventorys fetched: {product_inventorys_data}")
        response = generate_success_response("Filtered product_inventorys fetched successfully")
        response["records"] = product_inventorys_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_product_inventorys: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

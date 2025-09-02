from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.cart_item.model import CartItem
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


def create_cart_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating cart_item with content: {content}")
        if "cart_item" not in content:
            response = generate_bad_request_response(
                "CartItem data is required to create a cart_item."
            )
            return response
        cart_item = CartItem(**content["cart_item"].model_dump())
        status, cart_item_data = CartItem.add(cart_item)
        if not status:
            response = generate_not_acceptable_response("CartItem creation failed.")
            return response
        response = generate_success_response("cart_item created successfully")
        logger.success(f"CartItem created: {cart_item_data}")
        response["cart_item"] = cart_item_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_cart_item: {ex}")
    return response


def get_cart_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching cart_item with content: {content}")
        if "cart_item_id" not in content:
            response = generate_bad_request_response(
                "CartItem ID is required to fetch cart_item details."
            )
            return response
        status, cart_item = CartItem.get(content)
        if not status:
            response = generate_entity_not_found_response("CartItem")
            return response
        logger.success(f"CartItem fetched: {cart_item}")
        response = generate_success_response("cart_item fetched successfully")
        response["cart_item"] = cart_item
    except Exception as ex:
        logger.exception(f"Error in get_cart_item: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response 

def get_all_cart_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all cart_items with content: {content}")
        cart_item_data, all_cart_item_data = [], []
        _, all_cart_item_data = CartItem.get_all(content)
        if not all_cart_item_data:
            response = generate_entity_not_found_response("CartItems")
            return response
        for cart_item in all_cart_item_data:
            cart_item_data.append(cart_item.to_dict())
        logger.success(f"CartItems fetched: {cart_item_data}")
        response = generate_success_response("All cart_items fetched successfully")
        response["cart_item"] = cart_item_data
    except Exception as ex:
        logger.exception(f"Error in get_all_cart_items: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_cart_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating cart_item with content: {content}")
        updated_cart_item = None
        content["cart_item_id"] = content["cart_item"].cart_item_id
        status, cart_item_data = CartItem.get(content)
        if not status:
            response = generate_entity_not_found_response("CartItem")
            return response
        cart_item_data = CartItem(**cart_item_data)
        incoming_data = content["cart_item"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                cart_item_data.attributes = {**cart_item_data.attributes, **value}
            else:
                setattr(cart_item_data, key, value)
        cart_item_data.modified_at = content["cart_item"].modified_at
        status, updated_cart_item = CartItem.update(cart_item_data)
        if not status:
            response = generate_not_acceptable_response("CartItem update failed.")
            return response
        logger.success(f"CartItem updated: {updated_cart_item}")
        response = generate_success_response("cart_item updated successfully")
        response["cart_item"] = updated_cart_item
    except Exception as ex:
        logger.exception(f"Error in update_cart_item: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_cart_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting cart_item with content: {content}")
        if "cart_item_id" not in content:
            response = generate_bad_request_response(
                "CartItem ID is required to delete cart_item."
            )
            return response
        status, cart_item = CartItem.get(content)
        if not status:
            response = generate_entity_not_found_response("CartItem")
            return response
        cart_item_data = CartItem(**cart_item)

        # for hard delete
        # status = CartItem.delete(cart_item_data)

        # for soft delete
        if "cart_item" in content:
            cart_item.deleted_by = content["cart_item"].deleted_by
            cart_item.deleted_at = content["cart_item"].deleted_at
        elif "current_cart_item" in content:
            cart_item.deleted_by = content["current_cart_item"].cart_item_id
            cart_item.deleted_at = get_current_time()
            status, _ = CartItem.update(cart_item_data)
        if not status:
            response = generate_not_acceptable_response("CartItem deletion failed.")
            return response
        logger.success(f"CartItem deleted: {cart_item}")
        response = generate_success_response("cart_item deleted successfully")
        response["cart_item"] = cart_item
    except Exception as ex:
        logger.exception(f"Error in delete_cart_item: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_cart_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total cart_items with content: {content}")
        total_cart_items, search_criteria = 0, []
        cart_item_query = CartItem.query
        columns = inspect(CartItem).columns

        if not content.get("include_deleted"):
            cart_item_query = cart_item_query.filter(CartItem.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(CartItem, content["selected_column"], None)
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
        cart_item_query = cart_item_query.filter(or_(*search_criteria))
        total_cart_items = cart_item_query.count()
        logger.success(f"Total cart_items fetched: {total_cart_items}")
        response = generate_success_response("Total cart_items fetched successfully")
        response["total_cart_items"] = total_cart_items
    except Exception as ex:
        logger.exception(f"Error in get_total_cart_items: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_cart_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited cart_items with content: {content}")
        cart_items_data, cart_items, columns_list = [], None, None
        cart_item_query = CartItem.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(CartItem).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            cart_item_query = cart_item_query.filter(CartItem.deleted_by.is_(None))
        cart_items = (
            cart_item_query.order_by(desc(CartItem.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for cart_item in cart_items:
            cart_items_data.append(cart_item.to_dict())
        logger.success(f"CartItems fetched: {cart_items_data}")
        response = generate_success_response("Limited cart_items fetched successfully")
        response["records"] = cart_items_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_cart_items: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_cart_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered cart_items with content: {content}")
        cart_items_data, cart_items, columns_list, search_criteria = [], [], None, []
        cart_item_query = CartItem.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(CartItem).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(CartItem, content["selected_column"], None)
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
        cart_item_query = cart_item_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            cart_item_query = cart_item_query.filter(CartItem.deleted_by.is_(None))
        cart_items = (
            cart_item_query.order_by(desc(CartItem.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for cart_item in cart_items:
            cart_items_data.append(cart_item.to_dict())

        logger.success(f"CartItems fetched: {cart_items_data}")
        response = generate_success_response("Filtered cart_items fetched successfully")
        response["records"] = cart_items_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_cart_items: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

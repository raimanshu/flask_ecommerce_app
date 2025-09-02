from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.cart.model import Cart
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


def create_cart(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating cart with content: {content}")
        if "cart" not in content:
            response = generate_bad_request_response(
                "Cart data is required to create a cart."
            )
            return response
        cart = Cart(**content["cart"].model_dump())
        status, cart_data = Cart.add(cart)
        if not status:
            response = generate_not_acceptable_response("Cart creation failed.")
            return response
        response = generate_success_response("cart created successfully")
        logger.success(f"Cart created: {cart_data}")
        response["cart"] = cart_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_cart: {ex}")
    return response


def get_cart(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching cart with content: {content}")
        if "cart_id" not in content:
            response = generate_bad_request_response(
                "Cart ID is required to fetch cart details."
            )
            return response
        status, cart = Cart.get(content)
        if not status:
            response = generate_entity_not_found_response("Cart")
            return response
        logger.success(f"Cart fetched: {cart}")
        response = generate_success_response("cart fetched successfully")
        response["cart"] = cart
    except Exception as ex:
        logger.exception(f"Error in get_cart: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_carts(content):






    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all carts with content: {content}")
        cart_data, all_cart_data = [], []
        _, all_cart_data = Cart.get_all(content)
        if not all_cart_data:
            response = generate_entity_not_found_response("Carts")
            return response
        for cart in all_cart_data:
            cart_data.append(cart.to_dict())
        logger.success(f"Carts fetched: {cart_data}")
        response = generate_success_response("All carts fetched successfully")
        response["cart"] = cart_data
    except Exception as ex:
        logger.exception(f"Error in get_all_carts: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_cart(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating cart with content: {content}")
        updated_cart = None
        content["cart_id"] = content["cart"].cart_id
        status, cart_data = Cart.get(content)
        if not status:
            response = generate_entity_not_found_response("Cart")
            return response
        cart_data = Cart(**cart_data)
        incoming_data = content["cart"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                cart_data.attributes = {**cart_data.attributes, **value}
            else:
                setattr(cart_data, key, value)
        cart_data.modified_at = content["cart"].modified_at
        status, updated_cart = Cart.update(cart_data)
        if not status:
            response = generate_not_acceptable_response("Cart update failed.")
            return response
        logger.success(f"Cart updated: {updated_cart}")
        response = generate_success_response("cart updated successfully")
        response["cart"] = updated_cart
    except Exception as ex:
        logger.exception(f"Error in update_cart: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_cart(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting cart with content: {content}")
        if "cart_id" not in content:
            response = generate_bad_request_response(
                "Cart ID is required to delete cart."
            )
            return response
        status, cart = Cart.get(content)
        if not status:
            response = generate_entity_not_found_response("Cart")
            return response
        cart_data = Cart(**cart)

        # for hard delete
        # status = Cart.delete(cart_data)

        # for soft delete
        if "cart" in content:
            cart.deleted_by = content["cart"].deleted_by
            cart.deleted_at = content["cart"].deleted_at
        elif "current_cart" in content:
            cart.deleted_by = content["current_cart"].cart_id
            cart.deleted_at = get_current_time()
            status, _ = Cart.update(cart_data)
        if not status:
            response = generate_not_acceptable_response("Cart deletion failed.")
            return response
        logger.success(f"Cart deleted: {cart}")
        response = generate_success_response("cart deleted successfully")
        response["cart"] = cart
    except Exception as ex:
        logger.exception(f"Error in delete_cart: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_carts(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total carts with content: {content}")
        total_carts, search_criteria = 0, []
        cart_query = Cart.query
        columns = inspect(Cart).columns

        if not content.get("include_deleted"):
            cart_query = cart_query.filter(Cart.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Cart, content["selected_column"], None)
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
        cart_query = cart_query.filter(or_(*search_criteria))
        total_carts = cart_query.count()
        logger.success(f"Total carts fetched: {total_carts}")
        response = generate_success_response("Total carts fetched successfully")
        response["total_carts"] = total_carts
    except Exception as ex:
        logger.exception(f"Error in get_total_carts: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_carts(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited carts with content: {content}")
        carts_data, carts, columns_list = [], None, None
        cart_query = Cart.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Cart).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            cart_query = cart_query.filter(Cart.deleted_by.is_(None))
        carts = (
            cart_query.order_by(desc(Cart.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for cart in carts:
            carts_data.append(cart.to_dict())
        logger.success(f"Carts fetched: {carts_data}")
        response = generate_success_response("Limited carts fetched successfully")
        response["records"] = carts_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_carts: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_carts(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered carts with content: {content}")
        carts_data, carts, columns_list, search_criteria = [], [], None, []
        cart_query = Cart.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Cart).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Cart, content["selected_column"], None)
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
        cart_query = cart_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            cart_query = cart_query.filter(Cart.deleted_by.is_(None))
        carts = (
            cart_query.order_by(desc(Cart.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for cart in carts:
            carts_data.append(cart.to_dict())

        logger.success(f"Carts fetched: {carts_data}")
        response = generate_success_response("Filtered carts fetched successfully")
        response["records"] = carts_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_carts: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

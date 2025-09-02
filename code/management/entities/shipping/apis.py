from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.shipping.model import Shipping
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


def create_shipping(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating shipping with content: {content}")
        if "shipping" not in content:
            response = generate_bad_request_response(
                "Shipping data is required to create a shipping."
            )
            return response
        shipping = Shipping(**content["shipping"].model_dump())
        status, shipping_data = Shipping.add(shipping)
        if not status:
            response = generate_not_acceptable_response("Shipping creation failed.")
            return response
        response = generate_success_response("shipping created successfully")
        logger.success(f"Shipping created: {shipping_data}")
        response["shipping"] = shipping_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_shipping: {ex}")
    return response


def get_shipping(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching shipping with content: {content}")
        if "shipping_id" not in content:
            response = generate_bad_request_response(
                "Shipping ID is required to fetch shipping details."
            )
            return response
        status, shipping = Shipping.get(content)
        if not status:
            response = generate_entity_not_found_response("Shipping")
            return response
        logger.success(f"Shipping fetched: {shipping}")
        response = generate_success_response("shipping fetched successfully")
        response["shipping"] = shipping
    except Exception as ex:
        logger.exception(f"Error in get_shipping: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_shippings(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all shippings with content: {content}")
        shipping_data, all_shipping_data = [], []
        _, all_shipping_data = Shipping.get_all(content)
        if not all_shipping_data:
            response = generate_entity_not_found_response("Shippings")
            return response
        for shipping in all_shipping_data:
            shipping_data.append(shipping.to_dict())
        logger.success(f"Shippings fetched: {shipping_data}")
        response = generate_success_response("All shippings fetched successfully")
        response["shipping"] = shipping_data
    except Exception as ex:
        logger.exception(f"Error in get_all_shippings: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_shipping(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating shipping with content: {content}")
        updated_shipping = None
        content["shipping_id"] = content["shipping"].shipping_id
        status, shipping_data = Shipping.get(content)
        if not status:
            response = generate_entity_not_found_response("Shipping")
            return response
        shipping_data = Shipping(**shipping_data)
        incoming_data = content["shipping"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                shipping_data.attributes = {**shipping_data.attributes, **value}
            else:
                setattr(shipping_data, key, value)
        shipping_data.modified_at = content["shipping"].modified_at
        status, updated_shipping = Shipping.update(shipping_data)
        if not status:
            response = generate_not_acceptable_response("Shipping update failed.")
            return response
        logger.success(f"Shipping updated: {updated_shipping}")
        response = generate_success_response("shipping updated successfully")
        response["shipping"] = updated_shipping
    except Exception as ex:
        logger.exception(f"Error in update_shipping: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_shipping(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting shipping with content: {content}")
        if "shipping_id" not in content:
            response = generate_bad_request_response(
                "Shipping ID is required to delete shipping."
            )
            return response
        status, shipping = Shipping.get(content)
        if not status:
            response = generate_entity_not_found_response("Shipping")
            return response
        shipping_data = Shipping(**shipping)

        # for hard delete
        # status = Shipping.delete(shipping_data)

        # for soft delete
        if "shipping" in content:
            shipping.deleted_by = content["shipping"].deleted_by
            shipping.deleted_at = content["shipping"].deleted_at
        elif "current_shipping" in content:
            shipping.deleted_by = content["current_shipping"].shipping_id
            shipping.deleted_at = get_current_time()
            status, _ = Shipping.update(shipping_data)
        if not status:
            response = generate_not_acceptable_response("Shipping deletion failed.")
            return response
        logger.success(f"Shipping deleted: {shipping}")
        response = generate_success_response("shipping deleted successfully")
        response["shipping"] = shipping
    except Exception as ex:
        logger.exception(f"Error in delete_shipping: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_shippings(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total shippings with content: {content}")
        total_shippings, search_criteria = 0, []
        shipping_query = Shipping.query
        columns = inspect(Shipping).columns

        if not content.get("include_deleted"):
            shipping_query = shipping_query.filter(Shipping.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Shipping, content["selected_column"], None)
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
        shipping_query = shipping_query.filter(or_(*search_criteria))
        total_shippings = shipping_query.count()
        logger.success(f"Total shippings fetched: {total_shippings}")
        response = generate_success_response("Total shippings fetched successfully")
        response["total_shippings"] = total_shippings
    except Exception as ex:
        logger.exception(f"Error in get_total_shippings: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_shippings(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited shippings with content: {content}")
        shippings_data, shippings, columns_list = [], None, None
        shipping_query = Shipping.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Shipping).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            shipping_query = shipping_query.filter(Shipping.deleted_by.is_(None))
        shippings = (
            shipping_query.order_by(desc(Shipping.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for shipping in shippings:
            shippings_data.append(shipping.to_dict())
        logger.success(f"Shippings fetched: {shippings_data}")
        response = generate_success_response("Limited shippings fetched successfully")
        response["records"] = shippings_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_shippings: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_shippings(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered shippings with content: {content}")
        shippings_data, shippings, columns_list, search_criteria = [], [], None, []
        shipping_query = Shipping.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Shipping).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Shipping, content["selected_column"], None)
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
        shipping_query = shipping_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            shipping_query = shipping_query.filter(Shipping.deleted_by.is_(None))
        shippings = (
            shipping_query.order_by(desc(Shipping.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for shipping in shippings:
            shippings_data.append(shipping.to_dict())

        logger.success(f"Shippings fetched: {shippings_data}")
        response = generate_success_response("Filtered shippings fetched successfully")
        response["records"] = shippings_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_shippings: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

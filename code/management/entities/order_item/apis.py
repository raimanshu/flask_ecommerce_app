from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.order_item.model import OrderItem
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


def create_order_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating order_item with content: {content}")
        if "order_item" not in content:
            response = generate_bad_request_response(
                "OrderItem data is required to create a order_item."
            )
            return response
        order_item = OrderItem(**content["order_item"].model_dump())
        status, order_item_data = OrderItem.add(order_item)
        if not status:
            response = generate_not_acceptable_response("OrderItem creation failed.")
            return response
        response = generate_success_response("order_item created successfully")
        logger.success(f"OrderItem created: {order_item_data}")
        response["order_item"] = order_item_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_order_item: {ex}")
    return response


def get_order_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching order_item with content: {content}")
        if "order_item_id" not in content:
            response = generate_bad_request_response(
                "OrderItem ID is required to fetch order_item details."
            )
            return response
        status, order_item = OrderItem.get(content)
        if not status:
            response = generate_entity_not_found_response("OrderItem")
            return response
        logger.success(f"OrderItem fetched: {order_item}")
        response = generate_success_response("order_item fetched successfully")
        response["order_item"] = order_item
    except Exception as ex:
        logger.exception(f"Error in get_order_item: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_order_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all order_items with content: {content}")
        order_item_data, all_order_item_data = [], []
        _, all_order_item_data = OrderItem.get_all(content)
        if not all_order_item_data:
            response = generate_entity_not_found_response("OrderItems")
            return response
        for order_item in all_order_item_data:
            order_item_data.append(order_item.to_dict())
        logger.success(f"OrderItems fetched: {order_item_data}")
        response = generate_success_response("All order_items fetched successfully")
        response["order_item"] = order_item_data
    except Exception as ex:
        logger.exception(f"Error in get_all_order_items: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_order_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating order_item with content: {content}")
        updated_order_item = None
        content["order_item_id"] = content["order_item"].order_item_id
        status, order_item_data = OrderItem.get(content)
        if not status:
            response = generate_entity_not_found_response("OrderItem")
            return response
        order_item_data = OrderItem(**order_item_data)
        incoming_data = content["order_item"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                order_item_data.attributes = {**order_item_data.attributes, **value}
            else:
                setattr(order_item_data, key, value)
        order_item_data.modified_at = content["order_item"].modified_at
        status, updated_order_item = OrderItem.update(order_item_data)
        if not status:
            response = generate_not_acceptable_response("OrderItem update failed.")
            return response
        logger.success(f"OrderItem updated: {updated_order_item}")
        response = generate_success_response("order_item updated successfully")
        response["order_item"] = updated_order_item
    except Exception as ex:
        logger.exception(f"Error in update_order_item: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_order_item(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting order_item with content: {content}")
        if "order_item_id" not in content:
            response = generate_bad_request_response(
                "OrderItem ID is required to delete order_item."
            )
            return response
        status, order_item = OrderItem.get(content)
        if not status:
            response = generate_entity_not_found_response("OrderItem")
            return response
        order_item_data = OrderItem(**order_item)

        # for hard delete
        # status = OrderItem.delete(order_item_data)

        # for soft delete
        if "order_item" in content:
            order_item.deleted_by = content["order_item"].deleted_by
            order_item.deleted_at = content["order_item"].deleted_at
        elif "current_order_item" in content:
            order_item.deleted_by = content["current_order_item"].order_item_id
            order_item.deleted_at = get_current_time()
            status, _ = OrderItem.update(order_item_data)
        if not status:
            response = generate_not_acceptable_response("OrderItem deletion failed.")
            return response
        logger.success(f"OrderItem deleted: {order_item}")
        response = generate_success_response("order_item deleted successfully")
        response["order_item"] = order_item
    except Exception as ex:
        logger.exception(f"Error in delete_order_item: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_order_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total order_items with content: {content}")
        total_order_items, search_criteria = 0, []
        order_item_query = OrderItem.query
        columns = inspect(OrderItem).columns

        if not content.get("include_deleted"):
            order_item_query = order_item_query.filter(OrderItem.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(OrderItem, content["selected_column"], None)
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
        order_item_query = order_item_query.filter(or_(*search_criteria))
        total_order_items = order_item_query.count()
        logger.success(f"Total order_items fetched: {total_order_items}")
        response = generate_success_response("Total order_items fetched successfully")
        response["total_order_items"] = total_order_items
    except Exception as ex:
        logger.exception(f"Error in get_total_order_items: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_order_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited order_items with content: {content}")
        order_items_data, order_items, columns_list = [], None, None
        order_item_query = OrderItem.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(OrderItem).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            order_item_query = order_item_query.filter(OrderItem.deleted_by.is_(None))
        order_items = (
            order_item_query.order_by(desc(OrderItem.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for order_item in order_items:
            order_items_data.append(order_item.to_dict())
        logger.success(f"OrderItems fetched: {order_items_data}")
        response = generate_success_response("Limited order_items fetched successfully")
        response["records"] = order_items_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_order_items: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_order_items(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered order_items with content: {content}")
        order_items_data, order_items, columns_list, search_criteria = [], [], None, []
        order_item_query = OrderItem.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(OrderItem).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(OrderItem, content["selected_column"], None)
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
        order_item_query = order_item_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            order_item_query = order_item_query.filter(OrderItem.deleted_by.is_(None))
        order_items = (
            order_item_query.order_by(desc(OrderItem.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for order_item in order_items:
            order_items_data.append(order_item.to_dict())

        logger.success(f"OrderItems fetched: {order_items_data}")
        response = generate_success_response("Filtered order_items fetched successfully")
        response["records"] = order_items_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_order_items: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

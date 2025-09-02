from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.order.model import Order
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


def create_order(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating order with content: {content}")
        if "order" not in content:
            response = generate_bad_request_response(
                "Order data is required to create a order."
            )
            return response
        order = Order(**content["order"].model_dump())
        status, order_data = Order.add(order)
        if not status:
            response = generate_not_acceptable_response("Order creation failed.")
            return response
        response = generate_success_response("order created successfully")
        logger.success(f"Order created: {order_data}")
        response["order"] = order_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_order: {ex}")
    return response


def get_order(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching order with content: {content}")
        if "order_id" not in content:
            response = generate_bad_request_response(
                "Order ID is required to fetch order details."
            )
            return response
        status, order = Order.get(content)
        if not status:
            response = generate_entity_not_found_response("Order")
            return response
        logger.success(f"Order fetched: {order}")
        response = generate_success_response("order fetched successfully")
        response["order"] = order
    except Exception as ex:
        logger.exception(f"Error in get_order: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_orders(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all orders with content: {content}")
        order_data, all_order_data = [], []
        _, all_order_data = Order.get_all(content)
        if not all_order_data:
            response = generate_entity_not_found_response("Orders")
            return response
        for order in all_order_data:
            order_data.append(order.to_dict())
        logger.success(f"Orders fetched: {order_data}")
        response = generate_success_response("All orders fetched successfully")
        response["order"] = order_data
    except Exception as ex:
        logger.exception(f"Error in get_all_orders: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_order(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating order with content: {content}")
        updated_order = None
        content["order_id"] = content["order"].order_id
        status, order_data = Order.get(content)
        if not status:
            response = generate_entity_not_found_response("Order")
            return response
        order_data = Order(**order_data)
        incoming_data = content["order"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                order_data.attributes = {**order_data.attributes, **value}
            else:
                setattr(order_data, key, value)
        order_data.modified_at = content["order"].modified_at
        status, updated_order = Order.update(order_data)
        if not status:
            response = generate_not_acceptable_response("Order update failed.")
            return response
        logger.success(f"Order updated: {updated_order}")
        response = generate_success_response("order updated successfully")
        response["order"] = updated_order
    except Exception as ex:
        logger.exception(f"Error in update_order: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_order(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting order with content: {content}")
        if "order_id" not in content:
            response = generate_bad_request_response(
                "Order ID is required to delete order."
            )
            return response
        status, order = Order.get(content)
        if not status:
            response = generate_entity_not_found_response("Order")
            return response
        order_data = Order(**order)

        # for hard delete
        # status = Order.delete(order_data)

        # for soft delete
        if "order" in content:
            order.deleted_by = content["order"].deleted_by
            order.deleted_at = content["order"].deleted_at
        elif "current_order" in content:
            order.deleted_by = content["current_order"].order_id
            order.deleted_at = get_current_time()
            status, _ = Order.update(order_data)
        if not status:
            response = generate_not_acceptable_response("Order deletion failed.")
            return response
        logger.success(f"Order deleted: {order}")
        response = generate_success_response("order deleted successfully")
        response["order"] = order
    except Exception as ex:
        logger.exception(f"Error in delete_order: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_orders(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total orders with content: {content}")
        total_orders, search_criteria = 0, []
        order_query = Order.query
        columns = inspect(Order).columns

        if not content.get("include_deleted"):
            order_query = order_query.filter(Order.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Order, content["selected_column"], None)
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
        order_query = order_query.filter(or_(*search_criteria))
        total_orders = order_query.count()
        logger.success(f"Total orders fetched: {total_orders}")
        response = generate_success_response("Total orders fetched successfully")
        response["total_orders"] = total_orders
    except Exception as ex:
        logger.exception(f"Error in get_total_orders: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_orders(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited orders with content: {content}")
        orders_data, orders, columns_list = [], None, None
        order_query = Order.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Order).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            order_query = order_query.filter(Order.deleted_by.is_(None))
        orders = (
            order_query.order_by(desc(Order.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for order in orders:
            orders_data.append(order.to_dict())
        logger.success(f"Orders fetched: {orders_data}")
        response = generate_success_response("Limited orders fetched successfully")
        response["records"] = orders_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_orders: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_orders(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered orders with content: {content}")
        orders_data, orders, columns_list, search_criteria = [], [], None, []
        order_query = Order.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Order).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Order, content["selected_column"], None)
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
        order_query = order_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            order_query = order_query.filter(Order.deleted_by.is_(None))
        orders = (
            order_query.order_by(desc(Order.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for order in orders:
            orders_data.append(order.to_dict())

        logger.success(f"Orders fetched: {orders_data}")
        response = generate_success_response("Filtered orders fetched successfully")
        response["records"] = orders_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_orders: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

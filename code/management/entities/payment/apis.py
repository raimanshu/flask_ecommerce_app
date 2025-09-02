from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.payment.model import Payment
from utils.utility import (
    generate_bad_request_response,
    generate_entity_not_found_response,
    generate_internal_server_error_response,
    generate_not_acceptable_response,
    generate_success_response,
    generate_service_unavailable_error_response,
    extract_query_params,
    get_current_time,
)
from sqlalchemy import String, cast, desc, or_
from sqlalchemy.inspection import inspect
from infra.logging import logger


def create_payment(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating payment with content: {content}")
        if "payment" not in content:
            response = generate_bad_request_response(
                "Payment data is required to create a payment."
            )
            return response
        payment = Payment(**content["payment"].model_dump())
        status, payment_data = Payment.add(payment)
        if not status:
            response = generate_not_acceptable_response("Payment creation failed.")
            return response
        response = generate_success_response("payment created successfully")
        logger.success(f"Payment created: {payment_data}")
        response["payment"] = payment_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_payment: {ex}")
    return response


def get_payment(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching payment with content: {content}")
        if "payment_id" not in content:
            response = generate_bad_request_response(
                "Payment ID is required to fetch payment details."
            )
            return response
        status, payment = Payment.get(content)
        if not status:
            response = generate_entity_not_found_response("Payment")
            return response
        logger.success(f"Payment fetched: {payment}")
        response = generate_success_response("payment fetched successfully")
        response["payment"] = payment
    except Exception as ex:
        logger.exception(f"Error in get_payment: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_payments(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all payments with content: {content}")
        payment_data, all_payment_data = [], []
        _, all_payment_data = Payment.get_all(content)
        if not all_payment_data:
            response = generate_entity_not_found_response("Payments")
            return response
        for payment in all_payment_data:
            payment_data.append(payment.to_dict())
        logger.success(f"Payments fetched: {payment_data}")
        response = generate_success_response("All payments fetched successfully")
        response["payment"] = payment_data
    except Exception as ex:
        logger.exception(f"Error in get_all_payments: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_payment(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating payment with content: {content}")
        updated_payment = None
        content["payment_id"] = content["payment"].payment_id
        status, payment_data = Payment.get(content)
        if not status:
            response = generate_entity_not_found_response("Payment")
            return response
        payment_data = Payment(**payment_data)
        incoming_data = content["payment"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                payment_data.attributes = {**payment_data.attributes, **value}
            else:
                setattr(payment_data, key, value)
        payment_data.modified_at = content["payment"].modified_at
        status, updated_payment = Payment.update(payment_data)
        if not status:
            response = generate_not_acceptable_response("Payment update failed.")
            return response
        logger.success(f"Payment updated: {updated_payment}")
        response = generate_success_response("payment updated successfully")
        response["payment"] = updated_payment
    except Exception as ex:
        logger.exception(f"Error in update_payment: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_payment(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting payment with content: {content}")
        if "payment_id" not in content:
            response = generate_bad_request_response(
                "Payment ID is required to delete payment."
            )
            return response
        status, payment = Payment.get(content)
        if not status:
            response = generate_entity_not_found_response("Payment")
            return response
        payment_data = Payment(**payment)

        # for hard delete
        # status = Payment.delete(payment_data)

        # for soft delete
        if "payment" in content:
            payment.deleted_by = content["payment"].deleted_by
            payment.deleted_at = content["payment"].deleted_at
        elif "current_payment" in content:
            payment.deleted_by = content["current_payment"].payment_id
            payment.deleted_at = get_current_time()
            status, _ = Payment.update(payment_data)
        if not status:
            response = generate_not_acceptable_response("Payment deletion failed.")
            return response
        logger.success(f"Payment deleted: {payment}")
        response = generate_success_response("payment deleted successfully")
        response["payment"] = payment
    except Exception as ex:
        logger.exception(f"Error in delete_payment: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_payments(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total payments with content: {content}")
        total_payments, search_criteria = 0, []
        payment_query = Payment.query
        columns = inspect(Payment).columns

        if not content.get("include_deleted"):
            payment_query = payment_query.filter(Payment.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Payment, content["selected_column"], None)
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
        payment_query = payment_query.filter(or_(*search_criteria))
        total_payments = payment_query.count()
        logger.success(f"Total payments fetched: {total_payments}")
        response = generate_success_response("Total payments fetched successfully")
        response["total_payments"] = total_payments
    except Exception as ex:
        logger.exception(f"Error in get_total_payments: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_payments(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited payments with content: {content}")
        payments_data, payments, columns_list = [], None, None
        payment_query = Payment.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Payment).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            payment_query = payment_query.filter(Payment.deleted_by.is_(None))
        payments = (
            payment_query.order_by(desc(Payment.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for payment in payments:
            payments_data.append(payment.to_dict())
        logger.success(f"Payments fetched: {payments_data}")
        response = generate_success_response("Limited payments fetched successfully")
        response["records"] = payments_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_payments: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_payments(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered payments with content: {content}")
        payments_data, payments, columns_list, search_criteria = [], [], None, []
        payment_query = Payment.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Payment).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Payment, content["selected_column"], None)
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
        payment_query = payment_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            payment_query = payment_query.filter(Payment.deleted_by.is_(None))
        payments = (
            payment_query.order_by(desc(Payment.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for payment in payments:
            payments_data.append(payment.to_dict())

        logger.success(f"Payments fetched: {payments_data}")
        response = generate_success_response("Filtered payments fetched successfully")
        response["records"] = payments_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_payments: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

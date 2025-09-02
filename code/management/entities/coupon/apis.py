from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.coupon.model import Coupon
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


def create_coupon(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating coupon with content: {content}")
        if "coupon" not in content:
            response = generate_bad_request_response(
                "Coupon data is required to create a coupon."
            )
            return response
        coupon = Coupon(**content["coupon"].model_dump())
        status, coupon_data = Coupon.add(coupon)
        if not status:
            response = generate_not_acceptable_response("Coupon creation failed.")
            return response
        response = generate_success_response("coupon created successfully")
        logger.success(f"Coupon created: {coupon_data}")
        response["coupon"] = coupon_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_coupon: {ex}")
    return response


def get_coupon(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching coupon with content: {content}")
        if "coupon_id" not in content:
            response = generate_bad_request_response(
                "Coupon ID is required to fetch coupon details."
            )
            return response
        status, coupon = Coupon.get(content)
        if not status:
            response = generate_entity_not_found_response("Coupon")
            return response
        logger.success(f"Coupon fetched: {coupon}")
        response = generate_success_response("coupon fetched successfully")
        response["coupon"] = coupon
    except Exception as ex:
        logger.exception(f"Error in get_coupon: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_coupons(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all coupons with content: {content}")
        coupon_data, all_coupon_data = [], []
        _, all_coupon_data = Coupon.get_all(content)
        if not all_coupon_data:
            response = generate_entity_not_found_response("Coupons")
            return response
        for coupon in all_coupon_data:
            coupon_data.append(coupon.to_dict())
        logger.success(f"Coupons fetched: {coupon_data}")
        response = generate_success_response("All coupons fetched successfully")
        response["coupon"] = coupon_data
    except Exception as ex:
        logger.exception(f"Error in get_all_coupons: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_coupon(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating coupon with content: {content}")
        updated_coupon = None
        content["coupon_id"] = content["coupon"].coupon_id
        status, coupon_data = Coupon.get(content)
        if not status:
            response = generate_entity_not_found_response("Coupon")
            return response
        coupon_data = Coupon(**coupon_data)
        incoming_data = content["coupon"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                coupon_data.attributes = {**coupon_data.attributes, **value}
            else:
                setattr(coupon_data, key, value)
        coupon_data.modified_at = content["coupon"].modified_at
        status, updated_coupon = Coupon.update(coupon_data)
        if not status:
            response = generate_not_acceptable_response("Coupon update failed.")
            return response
        logger.success(f"Coupon updated: {updated_coupon}")
        response = generate_success_response("coupon updated successfully")
        response["coupon"] = updated_coupon
    except Exception as ex:
        logger.exception(f"Error in update_coupon: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_coupon(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting coupon with content: {content}")
        if "coupon_id" not in content:
            response = generate_bad_request_response(
                "Coupon ID is required to delete coupon."
            )
            return response
        status, coupon = Coupon.get(content)
        if not status:
            response = generate_entity_not_found_response("Coupon")
            return response
        coupon_data = Coupon(**coupon)

        # for hard delete
        # status = Coupon.delete(coupon_data)

        # for soft delete
        if "coupon" in content:
            coupon.deleted_by = content["coupon"].deleted_by
            coupon.deleted_at = content["coupon"].deleted_at
        elif "current_coupon" in content:
            coupon.deleted_by = content["current_coupon"].coupon_id
            coupon.deleted_at = get_current_time()
            status, _ = Coupon.update(coupon_data)
        if not status:
            response = generate_not_acceptable_response("Coupon deletion failed.")
            return response
        logger.success(f"Coupon deleted: {coupon}")
        response = generate_success_response("coupon deleted successfully")
        response["coupon"] = coupon
    except Exception as ex:
        logger.exception(f"Error in delete_coupon: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_coupons(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total coupons with content: {content}")
        total_coupons, search_criteria = 0, []
        coupon_query = Coupon.query
        columns = inspect(Coupon).columns

        if not content.get("include_deleted"):
            coupon_query = coupon_query.filter(Coupon.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Coupon, content["selected_column"], None)
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
        coupon_query = coupon_query.filter(or_(*search_criteria))
        total_coupons = coupon_query.count()
        logger.success(f"Total coupons fetched: {total_coupons}")
        response = generate_success_response("Total coupons fetched successfully")
        response["total_coupons"] = total_coupons
    except Exception as ex:
        logger.exception(f"Error in get_total_coupons: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_coupons(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited coupons with content: {content}")
        coupons_data, coupons, columns_list = [], None, None
        coupon_query = Coupon.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Coupon).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            coupon_query = coupon_query.filter(Coupon.deleted_by.is_(None))
        coupons = (
            coupon_query.order_by(desc(Coupon.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for coupon in coupons:
            coupons_data.append(coupon.to_dict())
        logger.success(f"Coupons fetched: {coupons_data}")
        response = generate_success_response("Limited coupons fetched successfully")
        response["records"] = coupons_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_coupons: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_coupons(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered coupons with content: {content}")
        coupons_data, coupons, columns_list, search_criteria = [], [], None, []
        coupon_query = Coupon.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Coupon).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Coupon, content["selected_column"], None)
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
        coupon_query = coupon_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            coupon_query = coupon_query.filter(Coupon.deleted_by.is_(None))
        coupons = (
            coupon_query.order_by(desc(Coupon.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for coupon in coupons:
            coupons_data.append(coupon.to_dict())

        logger.success(f"Coupons fetched: {coupons_data}")
        response = generate_success_response("Filtered coupons fetched successfully")
        response["records"] = coupons_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_coupons: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

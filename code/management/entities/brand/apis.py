from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.brand.model import Brand
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


def create_brand(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating brand with content: {content}")
        if "brand" not in content:
            response = generate_bad_request_response(
                "Brand data is required to create a brand."
            )
            return response
        brand = Brand(**content["brand"].model_dump())
        status, brand_data = Brand.add(brand)
        if not status:
            response = generate_not_acceptable_response("Brand creation failed.")
            return response
        response = generate_success_response("brand created successfully")
        logger.success(f"Brand created: {brand_data}")
        response["brand"] = brand_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_brand: {ex}")
    return response


def get_brand(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching brand with content: {content}")
        if "brand_id" not in content:
            response = generate_bad_request_response(
                "Brand ID is required to fetch brand details."
            )
            return response
        status, brand = Brand.get(content)
        if not status:
            response = generate_entity_not_found_response("Brand")
            return response
        logger.success(f"Brand fetched: {brand}")
        response = generate_success_response("brand fetched successfully")
        response["brand"] = brand
    except Exception as ex:
        logger.exception(f"Error in get_brand: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_brands(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all brands with content: {content}")
        brand_data, all_brand_data = [], []
        _, all_brand_data = Brand.get_all(content)
        if not all_brand_data:
            response = generate_entity_not_found_response("Brands")
            return response
        for brand in all_brand_data:
            brand_data.append(brand.to_dict())
        logger.success(f"Brands fetched: {brand_data}")
        response = generate_success_response("All brands fetched successfully")
        response["brand"] = brand_data
    except Exception as ex:
        logger.exception(f"Error in get_all_brands: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_brand(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating brand with content: {content}")
        updated_brand = None
        content["brand_id"] = content["brand"].brand_id
        status, brand_data = Brand.get(content)
        if not status:
            response = generate_entity_not_found_response("Brand")
            return response
        brand_data = Brand(**brand_data)
        incoming_data = content["brand"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                brand_data.attributes = {**brand_data.attributes, **value}
            else:
                setattr(brand_data, key, value)
        brand_data.modified_at = content["brand"].modified_at
        status, updated_brand = Brand.update(brand_data)
        if not status:
            response = generate_not_acceptable_response("Brand update failed.")
            return response
        logger.success(f"Brand updated: {updated_brand}")
        response = generate_success_response("brand updated successfully")
        response["brand"] = updated_brand
    except Exception as ex:
        logger.exception(f"Error in update_brand: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_brand(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting brand with content: {content}")
        if "brand_id" not in content:
            response = generate_bad_request_response(
                "Brand ID is required to delete brand."
            )
            return response
        status, brand = Brand.get(content)
        if not status:
            response = generate_entity_not_found_response("Brand")
            return response
        brand_data = Brand(**brand)

        # for hard delete
        # status = Brand.delete(brand_data)

        # for soft delete
        if "brand" in content:
            brand.deleted_by = content["brand"].deleted_by
            brand.deleted_at = content["brand"].deleted_at
        elif "current_brand" in content:
            brand.deleted_by = content["current_brand"].brand_id
            brand.deleted_at = get_current_time()
            status, _ = Brand.update(brand_data)
        if not status:
            response = generate_not_acceptable_response("Brand deletion failed.")
            return response
        logger.success(f"Brand deleted: {brand}")
        response = generate_success_response("brand deleted successfully")
        response["brand"] = brand
    except Exception as ex:
        logger.exception(f"Error in delete_brand: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_brands(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total brands with content: {content}")
        total_brands, search_criteria = 0, []
        brand_query = Brand.query
        columns = inspect(Brand).columns

        if not content.get("include_deleted"):
            brand_query = brand_query.filter(Brand.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Brand, content["selected_column"], None)
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
        brand_query = brand_query.filter(or_(*search_criteria))
        total_brands = brand_query.count()
        logger.success(f"Total brands fetched: {total_brands}")
        response = generate_success_response("Total brands fetched successfully")
        response["total_brands"] = total_brands
    except Exception as ex:
        logger.exception(f"Error in get_total_brands: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_brands(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited brands with content: {content}")
        brands_data, brands, columns_list = [], None, None
        brand_query = Brand.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Brand).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            brand_query = brand_query.filter(Brand.deleted_by.is_(None))
        brands = (
            brand_query.order_by(desc(Brand.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for brand in brands:
            brands_data.append(brand.to_dict())
        logger.success(f"Brands fetched: {brands_data}")
        response = generate_success_response("Limited brands fetched successfully")
        response["records"] = brands_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_brands: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_brands(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered brands with content: {content}")
        brands_data, brands, columns_list, search_criteria = [], [], None, []
        brand_query = Brand.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Brand).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Brand, content["selected_column"], None)
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
        brand_query = brand_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            brand_query = brand_query.filter(Brand.deleted_by.is_(None))
        brands = (
            brand_query.order_by(desc(Brand.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for brand in brands:
            brands_data.append(brand.to_dict())

        logger.success(f"Brands fetched: {brands_data}")
        response = generate_success_response("Filtered brands fetched successfully")
        response["records"] = brands_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_brands: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

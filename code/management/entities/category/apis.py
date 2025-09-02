from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.category.model import Category
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


def create_category(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating category with content: {content}")
        if "category" not in content:
            response = generate_bad_request_response(
                "Category data is required to create a category."
            )
            return response
        category = Category(**content["category"].model_dump())
        status, category_data = Category.add(category)
        if not status:
            response = generate_not_acceptable_response("Category creation failed.")
            return response
        response = generate_success_response("category created successfully")
        logger.success(f"Category created: {category_data}")
        response["category"] = category_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_category: {ex}")
    return response


def get_category(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching category with content: {content}")
        if "category_id" not in content:
            response = generate_bad_request_response(
                "Category ID is required to fetch category details."
            )
            return response
        status, category = Category.get(content)
        if not status:
            response = generate_entity_not_found_response("Category")
            return response
        logger.success(f"Category fetched: {category}")
        response = generate_success_response("category fetched successfully")
        response["category"] = category
    except Exception as ex:
        logger.exception(f"Error in get_category: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_categorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all categorys with content: {content}")
        category_data, all_category_data = [], []
        _, all_category_data = Category.get_all(content)
        if not all_category_data:
            response = generate_entity_not_found_response("Categorys")
            return response
        for category in all_category_data:
            category_data.append(category.to_dict())
        logger.success(f"Categorys fetched: {category_data}")
        response = generate_success_response("All categorys fetched successfully")
        response["category"] = category_data
    except Exception as ex:
        logger.exception(f"Error in get_all_categorys: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_category(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating category with content: {content}")
        updated_category = None
        content["category_id"] = content["category"].category_id
        status, category_data = Category.get(content)
        if not status:
            response = generate_entity_not_found_response("Category")
            return response
        category_data = Category(**category_data)
        incoming_data = content["category"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                category_data.attributes = {**category_data.attributes, **value}
            else:
                setattr(category_data, key, value)
        category_data.modified_at = content["category"].modified_at
        status, updated_category = Category.update(category_data)
        if not status:
            response = generate_not_acceptable_response("Category update failed.")
            return response
        logger.success(f"Category updated: {updated_category}")
        response = generate_success_response("category updated successfully")
        response["category"] = updated_category
    except Exception as ex:
        logger.exception(f"Error in update_category: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_category(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting category with content: {content}")
        if "category_id" not in content:
            response = generate_bad_request_response(
                "Category ID is required to delete category."
            )
            return response
        status, category = Category.get(content)
        if not status:
            response = generate_entity_not_found_response("Category")
            return response
        category_data = Category(**category)

        # for hard delete
        # status = Category.delete(category_data)

        # for soft delete
        if "category" in content:
            category.deleted_by = content["category"].deleted_by
            category.deleted_at = content["category"].deleted_at
        elif "current_category" in content:
            category.deleted_by = content["current_category"].category_id
            category.deleted_at = get_current_time()
            status, _ = Category.update(category_data)
        if not status:
            response = generate_not_acceptable_response("Category deletion failed.")
            return response
        logger.success(f"Category deleted: {category}")
        response = generate_success_response("category deleted successfully")
        response["category"] = category
    except Exception as ex:
        logger.exception(f"Error in delete_category: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_categorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total categorys with content: {content}")
        total_categorys, search_criteria = 0, []
        category_query = Category.query
        columns = inspect(Category).columns

        if not content.get("include_deleted"):
            category_query = category_query.filter(Category.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Category, content["selected_column"], None)
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
        category_query = category_query.filter(or_(*search_criteria))
        total_categorys = category_query.count()
        logger.success(f"Total categorys fetched: {total_categorys}")
        response = generate_success_response("Total categorys fetched successfully")
        response["total_categorys"] = total_categorys
    except Exception as ex:
        logger.exception(f"Error in get_total_categorys: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_categorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited categorys with content: {content}")
        categorys_data, categorys, columns_list = [], None, None
        category_query = Category.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Category).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            category_query = category_query.filter(Category.deleted_by.is_(None))
        categorys = (
            category_query.order_by(desc(Category.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for category in categorys:
            categorys_data.append(category.to_dict())
        logger.success(f"Categorys fetched: {categorys_data}")
        response = generate_success_response("Limited categorys fetched successfully")
        response["records"] = categorys_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_categorys: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_categorys(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered categorys with content: {content}")
        categorys_data, categorys, columns_list, search_criteria = [], [], None, []
        category_query = Category.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Category).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Category, content["selected_column"], None)
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
        category_query = category_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            category_query = category_query.filter(Category.deleted_by.is_(None))
        categorys = (
            category_query.order_by(desc(Category.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for category in categorys:
            categorys_data.append(category.to_dict())

        logger.success(f"Categorys fetched: {categorys_data}")
        response = generate_success_response("Filtered categorys fetched successfully")
        response["records"] = categorys_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_categorys: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

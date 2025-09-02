from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.user.model import User
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


def create_user(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating user with content: {content}")
        if "user" not in content:
            response = generate_bad_request_response(
                "User data is required to create a user."
            )
            return response
        user = User(**content["user"].model_dump())
        status, user_data = User.add(user)
        if not status:
            response = generate_not_acceptable_response("User creation failed.")
            return response
        response = generate_success_response("user created successfully")
        logger.success(f"User created: {user_data}")
        response["user"] = user_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_user: {ex}")
    return response


def get_user(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching user with content: {content}")
        if "user_id" not in content:
            response = generate_bad_request_response(
                "User ID is required to fetch user details."
            )
            return response
        status, user = User.get(content)
        if not status:
            response = generate_entity_not_found_response("User")
            return response
        logger.success(f"User fetched: {user}")
        response = generate_success_response("user fetched successfully")
        response["user"] = user
    except Exception as ex:
        logger.exception(f"Error in get_user: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_users(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all users with content: {content}")
        user_data, all_user_data = [], []
        _, all_user_data = User.get_all(content)
        if not all_user_data:
            response = generate_entity_not_found_response("Users")
            return response
        for user in all_user_data:
            user_data.append(user.to_dict())
        logger.success(f"Users fetched: {user_data}")
        response = generate_success_response("All users fetched successfully")
        response["user"] = user_data
    except Exception as ex:
        logger.exception(f"Error in get_all_users: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_user(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating user with content: {content}")
        updated_user = None
        content["user_id"] = content["user"].user_id
        status, user_data = User.get(content)
        if not status:
            response = generate_entity_not_found_response("User")
            return response
        user_data = User(**user_data)
        incoming_data = content["user"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                user_data.attributes = {**user_data.attributes, **value}
            else:
                setattr(user_data, key, value)
        user_data.modified_at = content["user"].modified_at
        status, updated_user = User.update(user_data)
        if not status:
            response = generate_not_acceptable_response("User update failed.")
            return response
        logger.success(f"User updated: {updated_user}")
        response = generate_success_response("user updated successfully")
        response["user"] = updated_user
    except Exception as ex:
        logger.exception(f"Error in update_user: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_user(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting user with content: {content}")
        if "user_id" not in content:
            response = generate_bad_request_response(
                "User ID is required to delete user."
            )
            return response
        status, user = User.get(content)
        if not status:
            response = generate_entity_not_found_response("User")
            return response
        user_data = User(**user)

        # for hard delete
        # status = User.delete(user_data)

        # for soft delete
        if "user" in content:
            user.deleted_by = content["user"].deleted_by
            user.deleted_at = content["user"].deleted_at
        elif "current_user" in content:
            user.deleted_by = content["current_user"].user_id
            user.deleted_at = get_current_time()
            status, _ = User.update(user_data)
        if not status:
            response = generate_not_acceptable_response("User deletion failed.")
            return response
        logger.success(f"User deleted: {user}")
        response = generate_success_response("user deleted successfully")
        response["user"] = user
    except Exception as ex:
        logger.exception(f"Error in delete_user: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_users(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total users with content: {content}")
        total_users, search_criteria = 0, []
        user_query = User.query
        columns = inspect(User).columns

        if not content.get("include_deleted"):
            user_query = user_query.filter(User.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(User, content["selected_column"], None)
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
        user_query = user_query.filter(or_(*search_criteria))
        total_users = user_query.count()
        logger.success(f"Total users fetched: {total_users}")
        response = generate_success_response("Total users fetched successfully")
        response["total_users"] = total_users
    except Exception as ex:
        logger.exception(f"Error in get_total_users: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_users(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited users with content: {content}")
        users_data, users, columns_list = [], None, None
        user_query = User.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(User).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            user_query = user_query.filter(User.deleted_by.is_(None))
        users = (
            user_query.order_by(desc(User.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for user in users:
            users_data.append(user.to_dict())
        logger.success(f"Users fetched: {users_data}")
        response = generate_success_response("Limited users fetched successfully")
        response["records"] = users_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_users: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_users(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered users with content: {content}")
        users_data, users, columns_list, search_criteria = [], [], None, []
        user_query = User.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(User).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(User, content["selected_column"], None)
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
        user_query = user_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            user_query = user_query.filter(User.deleted_by.is_(None))
        users = (
            user_query.order_by(desc(User.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for user in users:
            users_data.append(user.to_dict())

        logger.success(f"Users fetched: {users_data}")
        response = generate_success_response("Filtered users fetched successfully")
        response["records"] = users_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_users: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

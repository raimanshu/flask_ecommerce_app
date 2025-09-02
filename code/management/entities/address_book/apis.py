from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.address_book.model import AddressBook
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


def create_address_book(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating address_book with content: {content}")
        if "address_book" not in content:
            response = generate_bad_request_response(
                "AddressBook data is required to create a address_book."
            )
            return response
        address_book = AddressBook(**content["address_book"].model_dump())
        status, address_book_data = AddressBook.add(address_book)
        if not status:
            response = generate_not_acceptable_response("AddressBook creation failed.")
            return response
        response = generate_success_response("address_book created successfully")
        logger.success(f"AddressBook created: {address_book_data}")
        response["address_book"] = address_book_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_address_book: {ex}")
    return response


def get_address_book(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching address_book with content: {content}")
        if "address_book_id" not in content:
            response = generate_bad_request_response(
                "AddressBook ID is required to fetch address_book details."
            )
            return response
        status, address_book = AddressBook.get(content)
        if not status:
            response = generate_entity_not_found_response("AddressBook")
            return response
        logger.success(f"AddressBook fetched: {address_book}")
        response = generate_success_response("address_book fetched successfully")
        response["address_book"] = address_book
    except Exception as ex:
        logger.exception(f"Error in get_address_book: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_address_books(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all address_books with content: {content}")
        address_book_data, all_address_book_data = [], []
        _, all_address_book_data = AddressBook.get_all(content)
        if not all_address_book_data:
            response = generate_entity_not_found_response("AddressBooks")
            return response
        for address_book in all_address_book_data:
            address_book_data.append(address_book.to_dict())
        logger.success(f"AddressBooks fetched: {address_book_data}")
        response = generate_success_response("All address_books fetched successfully")
        response["address_book"] = address_book_data
    except Exception as ex:
        logger.exception(f"Error in get_all_address_books: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_address_book(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating address_book with content: {content}")
        updated_address_book = None
        content["address_book_id"] = content["address_book"].address_book_id
        status, address_book_data = AddressBook.get(content)
        if not status:
            response = generate_entity_not_found_response("AddressBook")
            return response
        address_book_data = AddressBook(**address_book_data)
        incoming_data = content["address_book"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                address_book_data.attributes = {**address_book_data.attributes, **value}
            else:
                setattr(address_book_data, key, value)
        address_book_data.modified_at = content["address_book"].modified_at
        status, updated_address_book = AddressBook.update(address_book_data)
        if not status:
            response = generate_not_acceptable_response("AddressBook update failed.")
            return response
        logger.success(f"AddressBook updated: {updated_address_book}")
        response = generate_success_response("address_book updated successfully")
        response["address_book"] = updated_address_book
    except Exception as ex:
        logger.exception(f"Error in update_address_book: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_address_book(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting address_book with content: {content}")
        if "address_book_id" not in content:
            response = generate_bad_request_response(
                "AddressBook ID is required to delete address_book."
            )
            return response
        status, address_book = AddressBook.get(content)
        if not status:
            response = generate_entity_not_found_response("AddressBook")
            return response
        address_book_data = AddressBook(**address_book)

        # for hard delete
        # status = AddressBook.delete(address_book_data)

        # for soft delete
        if "address_book" in content:
            address_book.deleted_by = content["address_book"].deleted_by
            address_book.deleted_at = content["address_book"].deleted_at
        elif "current_address_book" in content:
            address_book.deleted_by = content["current_address_book"].address_book_id
            address_book.deleted_at = get_current_time()
            status, _ = AddressBook.update(address_book_data)
        if not status:
            response = generate_not_acceptable_response("AddressBook deletion failed.")
            return response
        logger.success(f"AddressBook deleted: {address_book}")
        response = generate_success_response("address_book deleted successfully")
        response["address_book"] = address_book
    except Exception as ex:
        logger.exception(f"Error in delete_address_book: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_address_books(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total address_books with content: {content}")
        total_address_books, search_criteria = 0, []
        address_book_query = AddressBook.query
        columns = inspect(AddressBook).columns

        if not content.get("include_deleted"):
            address_book_query = address_book_query.filter(AddressBook.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(AddressBook, content["selected_column"], None)
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
        address_book_query = address_book_query.filter(or_(*search_criteria))
        total_address_books = address_book_query.count()
        logger.success(f"Total address_books fetched: {total_address_books}")
        response = generate_success_response("Total address_books fetched successfully")
        response["total_address_books"] = total_address_books
    except Exception as ex:
        logger.exception(f"Error in get_total_address_books: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_address_books(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited address_books with content: {content}")
        address_books_data, address_books, columns_list = [], None, None
        address_book_query = AddressBook.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(AddressBook).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            address_book_query = address_book_query.filter(AddressBook.deleted_by.is_(None))
        address_books = (
            address_book_query.order_by(desc(AddressBook.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for address_book in address_books:
            address_books_data.append(address_book.to_dict())
        logger.success(f"AddressBooks fetched: {address_books_data}")
        response = generate_success_response("Limited address_books fetched successfully")
        response["records"] = address_books_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_address_books: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_address_books(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered address_books with content: {content}")
        address_books_data, address_books, columns_list, search_criteria = [], [], None, []
        address_book_query = AddressBook.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(AddressBook).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(AddressBook, content["selected_column"], None)
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
        address_book_query = address_book_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            address_book_query = address_book_query.filter(AddressBook.deleted_by.is_(None))
        address_books = (
            address_book_query.order_by(desc(AddressBook.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for address_book in address_books:
            address_books_data.append(address_book.to_dict())

        logger.success(f"AddressBooks fetched: {address_books_data}")
        response = generate_success_response("Filtered address_books fetched successfully")
        response["records"] = address_books_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_address_books: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

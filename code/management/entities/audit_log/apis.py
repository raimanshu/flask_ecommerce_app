from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.audit_log.model import AuditLog
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


def create_audit_log(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating audit_log with content: {content}")
        if "audit_log" not in content:
            response = generate_bad_request_response(
                "AuditLog data is required to create a audit_log."
            )
            return response
        audit_log = AuditLog(**content["audit_log"].model_dump())
        status, audit_log_data = AuditLog.add(audit_log)
        if not status:
            response = generate_not_acceptable_response("AuditLog creation failed.")
            return response
        response = generate_success_response("audit_log created successfully")
        logger.success(f"AuditLog created: {audit_log_data}")
        response["audit_log"] = audit_log_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_audit_log: {ex}")
    return response


def get_audit_log(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching audit_log with content: {content}")
        if "audit_log_id" not in content:
            response = generate_bad_request_response(
                "AuditLog ID is required to fetch audit_log details."
            )
            return response
        status, audit_log = AuditLog.get(content)
        if not status:
            response = generate_entity_not_found_response("AuditLog")
            return response
        logger.success(f"AuditLog fetched: {audit_log}")
        response = generate_success_response("audit_log fetched successfully")
        response["audit_log"] = audit_log
    except Exception as ex:
        logger.exception(f"Error in get_audit_log: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_audit_logs(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all audit_logs with content: {content}")
        audit_log_data, all_audit_log_data = [], []
        _, all_audit_log_data = AuditLog.get_all(content)
        if not all_audit_log_data:
            response = generate_entity_not_found_response("AuditLogs")
            return response
        for audit_log in all_audit_log_data:
            audit_log_data.append(audit_log.to_dict())
        logger.success(f"AuditLogs fetched: {audit_log_data}")
        response = generate_success_response("All audit_logs fetched successfully")
        response["audit_log"] = audit_log_data
    except Exception as ex:
        logger.exception(f"Error in get_all_audit_logs: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_audit_log(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating audit_log with content: {content}")
        updated_audit_log = None
        content["audit_log_id"] = content["audit_log"].audit_log_id
        status, audit_log_data = AuditLog.get(content)
        if not status:
            response = generate_entity_not_found_response("AuditLog")
            return response
        audit_log_data = AuditLog(**audit_log_data)
        incoming_data = content["audit_log"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                audit_log_data.attributes = {**audit_log_data.attributes, **value}
            else:
                setattr(audit_log_data, key, value)
        audit_log_data.modified_at = content["audit_log"].modified_at
        status, updated_audit_log = AuditLog.update(audit_log_data)
        if not status:
            response = generate_not_acceptable_response("AuditLog update failed.")
            return response
        logger.success(f"AuditLog updated: {updated_audit_log}")
        response = generate_success_response("audit_log updated successfully")
        response["audit_log"] = updated_audit_log
    except Exception as ex:
        logger.exception(f"Error in update_audit_log: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_audit_log(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting audit_log with content: {content}")
        if "audit_log_id" not in content:
            response = generate_bad_request_response(
                "AuditLog ID is required to delete audit_log."
            )
            return response
        status, audit_log = AuditLog.get(content)
        if not status:
            response = generate_entity_not_found_response("AuditLog")
            return response
        audit_log_data = AuditLog(**audit_log)

        # for hard delete
        # status = AuditLog.delete(audit_log_data)

        # for soft delete
        if "audit_log" in content:
            audit_log.deleted_by = content["audit_log"].deleted_by
            audit_log.deleted_at = content["audit_log"].deleted_at
        elif "current_audit_log" in content:
            audit_log.deleted_by = content["current_audit_log"].audit_log_id
            audit_log.deleted_at = get_current_time()
            status, _ = AuditLog.update(audit_log_data)
        if not status:
            response = generate_not_acceptable_response("AuditLog deletion failed.")
            return response
        logger.success(f"AuditLog deleted: {audit_log}")
        response = generate_success_response("audit_log deleted successfully")
        response["audit_log"] = audit_log
    except Exception as ex:
        logger.exception(f"Error in delete_audit_log: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_audit_logs(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total audit_logs with content: {content}")
        total_audit_logs, search_criteria = 0, []
        audit_log_query = AuditLog.query
        columns = inspect(AuditLog).columns

        if not content.get("include_deleted"):
            audit_log_query = audit_log_query.filter(AuditLog.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(AuditLog, content["selected_column"], None)
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
        audit_log_query = audit_log_query.filter(or_(*search_criteria))
        total_audit_logs = audit_log_query.count()
        logger.success(f"Total audit_logs fetched: {total_audit_logs}")
        response = generate_success_response("Total audit_logs fetched successfully")
        response["total_audit_logs"] = total_audit_logs
    except Exception as ex:
        logger.exception(f"Error in get_total_audit_logs: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_audit_logs(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited audit_logs with content: {content}")
        audit_logs_data, audit_logs, columns_list = [], None, None
        audit_log_query = AuditLog.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(AuditLog).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            audit_log_query = audit_log_query.filter(AuditLog.deleted_by.is_(None))
        audit_logs = (
            audit_log_query.order_by(desc(AuditLog.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for audit_log in audit_logs:
            audit_logs_data.append(audit_log.to_dict())
        logger.success(f"AuditLogs fetched: {audit_logs_data}")
        response = generate_success_response("Limited audit_logs fetched successfully")
        response["records"] = audit_logs_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_audit_logs: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_audit_logs(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered audit_logs with content: {content}")
        audit_logs_data, audit_logs, columns_list, search_criteria = [], [], None, []
        audit_log_query = AuditLog.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(AuditLog).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(AuditLog, content["selected_column"], None)
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
        audit_log_query = audit_log_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            audit_log_query = audit_log_query.filter(AuditLog.deleted_by.is_(None))
        audit_logs = (
            audit_log_query.order_by(desc(AuditLog.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for audit_log in audit_logs:
            audit_logs_data.append(audit_log.to_dict())

        logger.success(f"AuditLogs fetched: {audit_logs_data}")
        response = generate_success_response("Filtered audit_logs fetched successfully")
        response["records"] = audit_logs_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_audit_logs: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

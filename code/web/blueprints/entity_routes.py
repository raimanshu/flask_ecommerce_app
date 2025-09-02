from flask import Blueprint, jsonify, request
from utils.constants import DEFAULT_API_RESPONSE_OBJ, RESPONSE_CODE_KWD
from web.apis.api_handler import entity_operation
from utils.utility import get_request_paramenters, generate_internal_server_error_response, generate_success_response
from infra.logging import logger


entity_route = Blueprint("entity_route", __name__)


@entity_route.route("/status/", methods=["GET"])
def status():
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug("Status route called")
        response = generate_success_response("Route Status OK")
    except Exception as ex:
        logger.exception(f"Error in status: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return jsonify(response), response[RESPONSE_CODE_KWD]


@entity_route.route("/<entity_name>/<operation_name>/", methods=["GET"])
def entity_get_all_operation_route(**kwargs):

    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Get all operation route called with kwargs: {kwargs}")
        payload = {
            "query_params": request.args.to_dict(flat=False),
            "entity_name": kwargs["entity_name"],
            "operation_name": kwargs["operation_name"],
        }
        payload.update(get_request_paramenters(request.headers))
        response = entity_operation(
            kwargs["entity_name"], kwargs["operation_name"], payload
        )
    except Exception as ex:
        logger.exception(f"Error in get_all_operation_route: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return jsonify(response), response[RESPONSE_CODE_KWD]


@entity_route.route("/<entity_name>/<operation_name>/<entity_id>/", methods=["GET"])
def entity_get_operation_route(**kwargs):
    try:
        logger.debug(f"Get operation route called with kwargs: {kwargs}")
        payload = {
            f"{kwargs['entity_name']}_id": kwargs["entity_id"],
            "query_params": request.args.to_dict(flat=False),
            "entity_name": kwargs["entity_name"],
            "operation_name": kwargs["operation_name"],
        }
        payload.update(get_request_paramenters(request.headers))
        response = entity_operation(
            kwargs["entity_name"], kwargs["operation_name"], payload
        )
    except Exception as ex:
        logger.exception(f"Error in get_operation_route: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return jsonify(response), response[RESPONSE_CODE_KWD]


@entity_route.route("/<entity_name>/<operation_name>/<entity_id>", methods=["DELETE"])
def entity_delete_operation_route(**kwargs):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Delete operation route called with kwargs: {kwargs}")
        payload = {
            f"{kwargs['entity_name']}_id": kwargs["entity_id"],
            "entity_name": kwargs["entity_name"],
            "operation_name": kwargs["operation_name"],
        }
        payload.update(get_request_paramenters(request.headers))
        response = entity_operation(
            kwargs["entity_name"], kwargs["operation_name"], payload
        )
    except Exception as ex:
        logger.exception(f"Error in delete_operation_route: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return jsonify(response), response[RESPONSE_CODE_KWD]


@entity_route.route("/<entity_name>/<operation_name>/", methods=["POST"])
def entity_post_operation_route(**kwargs):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Post operation route called with kwargs: {kwargs}")
        payload = request.json
        payload = {
            "entity_name": kwargs["entity_name"],
            "operation_name": kwargs["operation_name"],
        }
        payload.update(get_request_paramenters(request.headers))
        response = entity_operation(
            kwargs["entity_name"], kwargs["operation_name"], payload
        )
    except Exception as ex:
        logger.exception(f"Error in post_operation_route: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return jsonify(response), response[RESPONSE_CODE_KWD]


@entity_route.route("/<entity_name>/<operation_name>/<entity_id>/", methods=["PUT"])
def entity_put_operation_route(**kwargs):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Put operation route called with kwargs: {kwargs}")
        payload = request.json
        payload = {
            f"{kwargs['entity_name']}_id": kwargs["entity_id"],
            "entity_name": kwargs["entity_name"],
            "operation_name": kwargs["operation_name"],
        }
        payload.update(get_request_paramenters(request.headers))
        response = entity_operation(
            kwargs["entity_name"], kwargs["operation_name"], payload
        )
    except Exception as ex:
        logger.exception(f"Error in put_operation_route: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return jsonify(response), response[RESPONSE_CODE_KWD]

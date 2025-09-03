

from flask import Blueprint, jsonify, request
from web.apis.api_handler import authentication_api_operation
from utils.utility import get_request_paramenters, generate_internal_server_error_response, generate_success_response
from utils.constants import DEFAULT_API_RESPONSE_OBJ, RESPONSE_CODE_KWD
from infra.logging import logger
from utils.config import validate_jwt_token, create_session


auth_route = Blueprint("auth_route", __name__)


@auth_route.route("/status/", methods=["GET"])
def status():
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug("Status route called")
        response = generate_success_response("Route Status OK")
    except Exception as ex:
        logger.exception(f"Error in status: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return jsonify(response), response[RESPONSE_CODE_KWD]

@auth_route.route("/login", methods=["POST"])
@create_session
def user_login_operation(**kwargs):
    try:
        logger.debug(f"Authentication Login API called : {kwargs}")
        payload = request.json
        # kwargs.update(get_request_paramenters(request.headers))
        kwargs["api_endpoint"] = "login"
        response = authentication_api_operation(payload, **kwargs)        
    except Exception as ex:
        response = generate_internal_server_error_response(str(ex))
        logger.exception(f"Error in user_login_operation: {ex}")
    return jsonify(response), response[RESPONSE_CODE_KWD]

@auth_route.route("/<api_endpoint>", methods=["GET"])
@create_session
@validate_jwt_token
def authentication_get_operation(**kwargs):
    try:
        logger.debug(f"Authentication GET API called : {kwargs}")
        payload = {}
        # kwargs.update(get_request_paramenters(request.headers))
        response = authentication_api_operation(payload, **kwargs)        
    except Exception as ex:
        response = generate_internal_server_error_response(str(ex))
        logger.exception(f"Error in user_login_operation: {ex}")
    return jsonify(response), response[RESPONSE_CODE_KWD]
    


from flask import Blueprint, jsonify, request
from infra.logging import logger
from utils.constants import DEFAULT_API_RESPONSE_OBJ, RESPONSE_CODE_KWD
from web.apis.api_handler import authentication_api_operation
from utils.utility import get_request_paramenters
from utils.utility import generate_internal_server_error_response


auth_route = Blueprint("auth_route", __name__)

@auth_route.route("/<api_endpoint>", methods=["POST"])
def user_login_operation(kwargs):
    try:
        logger.debug(f"Authentication API called : {kwargs}")
        payload = request.json
        kwargs.update(get_request_paramenters(request.headers))
        response = authentication_api_operation(payload, **kwargs)        
    except Exception as ex:
        response = generate_internal_server_error_response(str(ex))
        logger.exception(f"Error in user_login_operation: {ex}")
    return jsonify(response), response[RESPONSE_CODE_KWD]
    
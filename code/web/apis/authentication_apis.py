import jwt
import bcrypt
from datetime import timedelta


from infra.environment import SECRET_KEY
from infra.logging import logger
from utils.constants import DEFAULT_API_RESPONSE_OBJ, JWT_ACCESS_TOKEN_EXPIRES
from utils.utility import (
    generate_internal_server_error_response,
    generate_bad_request_response,
    generate_success_response,
    generate_entity_not_found_response,
)
from utils.utility import get_current_time, string_to_base64
from management.entities.user.model import UserProvider


def user_login(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Logging in user with content: {content}")
        user = None
        if content.get("email", ""):
            _, user = UserProvider.get_by_attribute("email", content)
            if not user:
                response = generate_bad_request_response("User not found.")
                return response
        else:
            response = generate_bad_request_response("Email is required to login user.")
            return response
        if content.get("password", ""):
            check_password = user and string_to_base64(content.get("password")) == user.password
            # check_password = user and bcrypt.checkpw(
            #     content.get("password").encode("utf-8"), user.password
            # )
            if not check_password:
                response = generate_bad_request_response("Invalid password.")
                return response
            response = generate_success_response("user logged in successfully.")
            token = jwt.encode(
                {
                    "user_id": user.user_id,
                    "created_at": str(get_current_time()),
                    "expiration": str(
                        get_current_time() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
                    ),
                },
                SECRET_KEY,
                algorithm="HS256",
            )
            user_dict = user.to_dict()
            # del user_dict["password"]
            response["data"] = {"user": user_dict, "token": token}
        else:
            response = generate_bad_request_response(
                "Password is required to login user."
            )
    except Exception as ex:
        logger.exception(f"Error logging in user: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def user_logout(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Logging out user with content: {content}")
        if not content.get("current_user", ""):
            response = generate_entity_not_found_response("user")
            return response
        current_time = get_current_time()
        content["current_user"].attributes["logged_out_time"] = str(current_time)
        # content["current_user"].attributes["logged_in_mac_address"] = get_mac_address()
        content["current_user"].attributes["logged_out_counter"] = (
            int(content["current_user"].attributes["logged_out_counter"]) + 1
            if "logged_out_counter" in content["current_user"].attributes
            else 1
        )
        content["current_user"].modified_at = current_time
        content["current_user"].modified_by = content["current_user"].user_id
        status = False
        status, _ = UserProvider.update(content["current_user"])
        if not status:
            response = generate_internal_server_error_response("User update failed.")
            return response
        response = generate_success_response("user logged out successfully")
    except Exception as ex:
        logger.exception(f"Error logging out user: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

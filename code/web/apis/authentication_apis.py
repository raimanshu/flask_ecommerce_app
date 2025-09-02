import jwt
from datetime import timedelta

from infra.environment import SECRET_KEY
from infra.logging import logger
from utils.constants import DEFAULT_API_RESPONSE_OBJ, JWT_ACCESS_TOKEN_EXPIRES
from utils.utility import (
    generate_internal_server_error_response,
    generate_bad_request_response,
    generate_success_response,
)
from utils.utility import get_current_time
from management.entities.user.model import UserProvider


def user_login(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Logging in user with content: {content}")
        user = None
        if content.get("email", ""):
            _, user = UserProvider.get_by_attribute("email", content)

        else:
            response = generate_bad_request_response("Email is required to login user.")
            return response
        if content.get("password", ""):
            check_password = user and content.get("password") == user.password
            if not check_password:
                response = generate_bad_request_response("Invalid password.")
                return response
            response = generate_success_response("user logged in successfully.")
            token = jwt.encode(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.name,
                    "username": user.username,
                    "expiration": str(
                        get_current_time() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
                    ),
                },
                SECRET_KEY,
                algorithm="HS256",
            )
            user_dict = user.to_dict()
            del user_dict["password"]
            response["data"] = {"user": user_dict, "token": token}
        else:
            response = generate_bad_request_response(
                "Password is required to login user."
            )
            return response
    except Exception as ex:
        logger.exception(f"Error logging in user: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def user_logout(content):
    pass

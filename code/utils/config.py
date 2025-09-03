from infra.logging import logger
from flask import request
from functools import wraps
from utils.utility import generate_bad_request_response, get_current_time, compare_dates
import jwt
from infra.environment import SECRET_KEY
from management.entities.user.model import UserProvider
from infra.db_router import set_current_db, get_session


def validate_jwt_token(func):
    @wraps(func)
    def validate_token(**kwargs):
        logger.debug(f"Validating JWT token: {kwargs}")
        token = False
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]

        if "token" in request.args:
            token = request.args.get("token")

        if not token:
            return generate_bad_request_response(
                error_msg="Authentication Token is missing!"
            )
        try:
            # kwargs["token"] = token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if compare_dates(get_current_time(), data["expiration"]) != "lesser":
                return generate_bad_request_response(
                    error_msg="Authentication Token is expired!"
                )

            current_user = None
            payload = {
                "user_id": data["user_id"],
                # "db_session": kwargs["db_session"],
                # "include_deleted": False,
            }
            _, current_user = UserProvider.get_by_attribute("user_id", payload)
            if current_user is None or (
                current_user.attributes
                and "logged_out_time" in current_user.attributes
                and current_user.attributes["logged_out_time"]
                and compare_dates(
                    current_user.attributes["logged_out_time"], data["created_at"]
                )
                == "greater"
            ):
                return generate_bad_request_response(
                    error_msg="Invalid Authentication token!"
                )
        except Exception as ex:
            logger.exception(f"Error in validate_token: {ex}")
            response = generate_bad_request_response(str(ex))
            return response
        kwargs["current_user"] = current_user
        logger.debug(f"Validated JWT token: {kwargs}")
        response = func(**kwargs)
        return response

    return validate_token


def create_session(func):
    @wraps(func)
    def create_default_session(**kwargs):
        try:
            logger.debug(f"Creating session: {kwargs}")
            db = "sqlite"
            kwargs["db"] = "sqlite"
            set_current_db("sqlite")
            kwargs["db_session"] = get_session()
        except Exception as ex:
            logger.exception(f"Error in create_default_session: {ex}")
            response = generate_bad_request_response(str(ex))
            return response
        logger.debug(f"Created session: {kwargs}")
        response = func(**kwargs)
        return response

    return create_default_session

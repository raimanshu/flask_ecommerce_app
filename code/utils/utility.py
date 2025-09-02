

import base64
import re
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone

from dateutil import parser

from infra.logging import logger

from utils.constants import (
    DEFAULT_API_RESPONSE_OBJ,    
    RESPONSE_CODE_KWD,
    RESPONSE_STATUS_KWD,
    RESPONSE_MSG_KWD,
    BAD_REQUEST_ERROR_MSG,
    INPUT_NOT_ACCEPTABLE_RESPONSE
)


# region REST APIs

def generate_bad_request_response(error_msg=BAD_REQUEST_ERROR_MSG):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    response[RESPONSE_CODE_KWD] = 400
    response[RESPONSE_STATUS_KWD] = False
    response[RESPONSE_MSG_KWD] = error_msg
    return response


def generate_entity_not_found_response(entity_name):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    response[RESPONSE_CODE_KWD] = 404
    response[RESPONSE_STATUS_KWD] = False
    response[RESPONSE_MSG_KWD] = (
        f"We are unable to find {entity_name} details in database."
    )
    return response


def generate_success_response(success_msg):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    response[RESPONSE_CODE_KWD] = 200
    response[RESPONSE_STATUS_KWD] = True
    response[RESPONSE_MSG_KWD] = success_msg
    return response


def generate_internal_server_error_response(error_msg):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    response[RESPONSE_CODE_KWD] = 500
    response[RESPONSE_STATUS_KWD] = False
    response[RESPONSE_MSG_KWD] = f"Internal Server Error: {error_msg}"
    return response


def generate_not_acceptable_response(
    entity_name, error_msg=INPUT_NOT_ACCEPTABLE_RESPONSE
):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    response[RESPONSE_CODE_KWD] = 406
    response[RESPONSE_STATUS_KWD] = False
    response[RESPONSE_MSG_KWD] = f"{error_msg} {entity_name}"
    return response


def generate_service_unavailable_error_response(error_msg):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    response[RESPONSE_CODE_KWD] = 503
    response[RESPONSE_STATUS_KWD] = False
    response[RESPONSE_MSG_KWD] = f"Service Unavailable: {error_msg}"
    return response


def get_request_paramenters(headers):
    return {
        "include_deleted": str(headers.get("Include-Deleted", "false")).lower()
        == "true",
        "resolve_enums": str(headers.get("Resolve-Enums", "false")).lower() == "true",
        "resolve_relationships": str(
            headers.get("Resolve-Relationships", "false")
        ).lower()
        == "true",
    }

def extract_query_params(content):
    result = {}
    query_params = content.get("query_params", {})

    for key, value_list in query_params.items():
        if isinstance(value_list, list) and value_list:
            cleaned_value = value_list[0].strip().strip('"')
            result[key] = cleaned_value
        else:
            result[key] = ""
    return result


# endregion

# region redis cache functions


# def create_entity_cache(entity_dict, entity_id, CACHE_ENTITY_KEYWORD):
#     """Create cache for an entity in Redis.

#     Args:
#         entity_dict (dict): Dictionary representing the entity data.
#         entity_id (str): Unique identifier for the entity.
#         CACHE_ENTITY_KEYWORD (str): Cache keyword for the entity.
#     """
#     try:
#         logger.debug(
#             f"Creating entity cache for: {CACHE_ENTITY_KEYWORD} having id: {entity_id} with data: {entity_dict}"
#         )
#         if entity_dict:
#             set_redis_hash_map(
#                 CACHE_ENTITY_KEYWORD,
#                 entity_id,
#                 json.dumps(entity_dict, cls=CustomJSONEncoder),
#             )
#             set_redis_expiry(CACHE_ENTITY_KEYWORD, CACHE_EXPIRE_TIME)
#     except Exception as ex:
#         logger.exception(f"Error occurred in create_entity_cache: {str(ex)}")


# def delete_entity_cache(entity_id, CACHE_ENTITY_KEYWORD):
#     """Delete cache for an entity from Redis.

#     Args:
#         entity_id (str): Unique identifier for the entity.
#         CACHE_ENTITY_KEYWORD (str): Cache keyword for the entity.
#     """
#     try:
#         logger.debug(
#             f"Deleting entity cache for: {CACHE_ENTITY_KEYWORD} having id: {entity_id}"
#         )
#         data = get_redis_hash_map(CACHE_ENTITY_KEYWORD, entity_id)
#         if data:
#             delete_redis_hash_map(CACHE_ENTITY_KEYWORD, entity_id)
#     except Exception as ex:
#         logger.exception(f"Error occurred in delete_entity_cache: {str(ex)}")


# def fetch_entity_cache(**kwargs):
#     """Fetch entity data from the cache in Redis.

#     Args:
#         **kwargs: Additional keyword arguments including 'entity_name', 'entity_id', 'db_tenant_engine'.

#     Returns:
#         dict: Response dictionary containing the fetched entity data or error response.
#     """
#     try:
#         logger.debug(f"Fetching entity cache from redis having arguments: {kwargs}")
#         entity_name = kwargs["entity_name"].upper()
#         CACHE_ENTITY_KEYWORD = globals()[f"CACHE_{entity_name}_KEYWORD"]
#         entity_data = get_redis_hash_map(CACHE_ENTITY_KEYWORD, kwargs["entity_id"])
#         if not entity_data:
#             return generate_entity_not_found_response(f"{kwargs['entity_name']}")
#         response = generate_success_response(
#             f"We have fetched {kwargs['entity_name']} details successfully."
#         )
#         response[kwargs["entity_name"]] = json.loads(entity_data)
#         logger.debug(f"We have fetched {kwargs['entity_name']} details successfully.")
#     except Exception as ex:
#         response = generate_internal_server_error_response(str(ex))
#     return response


# endregion


# region serialize datetime class


# class CustomJSONEncoder(json.JSONEncoder):
#     """Custom JSON encoder to handle datetime objects.

#     This encoder extends json.JSONEncoder and provides custom serialization
#     for datetime objects by converting them to ISO format strings.

#     Attributes:
#         default: Overrides the default method to handle datetime serialization.
#     """

#     def default(self, o):
#         """Serialize datetime objects to ISO format strings.

#         Args:
#             obj: The object to serialize.

#         Returns:
#             str: Serialized representation of the object, or passed to the parent class for default handling.
#         """
#         if isinstance(o, datetime):
#             return o.isoformat()
#         return super().default(o)


# endregion

# region otp function


# def generate_otp(length=6):
#     """Generate a random OTP (One Time Password) of the specified length.

#     Args:
#         length (int): Length of the OTP to be generated. Default is 6.

#     Returns:
#         str: A random OTP string consisting of digits.
#     """
#     digits = string.digits
#     otp = "".join(secrets.choice(digits) for _ in range(length))
#     return otp


# endregion


# region datetime/string functions


def get_current_time(with_seconds=True):
    _date = datetime.now(timezone.utc).replace(tzinfo=None)
    if not with_seconds:
        _date = _date.replace(second=0, microsecond=0)
    return _date


def transform_datetime_ist(date_time):
    return date_time + timedelta(hours=5, minutes=30)


def string_to_base64(password):
    return base64.b64encode(password.encode("utf-8")).decode("utf-8")


def base64_to_string(password):
    return base64.b64decode(password).decode("utf-8")


def generate_random_string(str_length=8):
    try:
        random_string = None
        logger.debug(f"Generating random string of length: {str_length}")
        alphabet = string.ascii_letters + string.digits
        random_string = "".join(secrets.choice(alphabet) for i in range(str_length))
    except Exception as ex:
        logger.exception(f"Error occurred while generating random string: {ex}")
    return random_string


def compare_dates(date1, date2):
    try:
        response = ""
        if isinstance(date1, str):
            date1 = datetime.strptime(date1, "%Y-%m-%d %H:%M:%S.%f")
        if isinstance(date2, str):
            date2 = datetime.strptime(date2, "%Y-%m-%d %H:%M:%S.%f")

        if date1 == date2:
            response = "equal"
        elif date1 > date2:
            response = "greater"
        else:
            response = "lesser"
    except Exception as ex:
        logger.exception(f"Error occurred while comparing dates: {ex}")
    return response


def get_mac_address():
    mac = uuid.getnode()
    mac_address = ":".join(
        [f"{(mac >> elements) & 0xFF:02x}" for elements in reversed(range(0, 48, 8))]
    )
    return mac_address


def string_to_date(date_str):
    try:
        date = parser.parse(date_str)
        formatted_date = date.strftime("01-%m-%Y")
        return True, formatted_date
    except (ValueError, OverflowError) as ex:
        logger.exception(f"Error occurred while converting string to date: {ex}")
        return False, None

def string_remove_special_character(file_name):
    name, ext = file_name.rsplit(".", 1)
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    file_name = f"{name}.{ext}"
    return file_name

# endregion
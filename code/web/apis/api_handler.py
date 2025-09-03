from utils.constants import DEFAULT_API_RESPONSE_OBJ
from web.blueprints.api_routes import ENTITY_API_ROUTES
from utils.utility import (
    generate_bad_request_response,
)
from infra.logging import logger
from web.blueprints.api_routes import AUTHENTICATION_API_ROUTES

def entity_operation(entity_name, operation_name, payload):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Entity: {entity_name}, Operation: {operation_name}, Payload: {payload}")
        if entity_name not in ENTITY_API_ROUTES:
            return ValueError(f"Entity {entity_name} not found.")
        if operation_name not in ENTITY_API_ROUTES[entity_name]:
            return ValueError(
                f"Operation {operation_name} not found for entity {entity_name}."
            )
        route = ENTITY_API_ROUTES[entity_name][operation_name]
        entity_data = {}
        if route["schema"]:
            entity_data[f"{entity_name}"] = _create_entity_data(route, payload)
            if not entity_data[f"{entity_name}"]:
                response = generate_bad_request_response()
                return response
            entity_data.update(payload)
            response = route["api"](entity_data)
        else:
            payload["operation_name"] = operation_name
            response = route["api"](payload)
    except Exception as ex:
        logger.exception(f"Error in entity_operation {entity_operation} in entity_name {entity_name}: {ex}")
    return response

def authentication_api_operation(payload, **kwargs):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(
            f"{kwargs['api_endpoint']} operation initiated having payload {payload}"
        )
        if kwargs["api_endpoint"] not in AUTHENTICATION_API_ROUTES:
            response = generate_bad_request_response()
            return response
        payload.update(kwargs)
        response = AUTHENTICATION_API_ROUTES[kwargs['api_endpoint']](payload)
    except Exception as ex:
        logger.exception(f"Error in authentication_api_operation: {ex}")
    return response


def _create_entity_data(route, payload):
    try:
        logger.debug(f"Creating entity_data object for route: {route}, payload: {payload}")
        entity_data = None
        entity_data = route["schema"](**payload)
    except Exception as ex:
        logger.exception(f"Error in _create_entity_data: {ex}")
    return entity_data

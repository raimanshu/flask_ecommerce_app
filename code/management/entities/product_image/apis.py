from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.product_image.model import ProductImage
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


def create_product_image(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating product_image with content: {content}")
        if "product_image" not in content:
            response = generate_bad_request_response(
                "ProductImage data is required to create a product_image."
            )
            return response
        product_image = ProductImage(**content["product_image"].model_dump())
        status, product_image_data = ProductImage.add(product_image)
        if not status:
            response = generate_not_acceptable_response("ProductImage creation failed.")
            return response
        response = generate_success_response("product_image created successfully")
        logger.success(f"ProductImage created: {product_image_data}")
        response["product_image"] = product_image_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_product_image: {ex}")
    return response


def get_product_image(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching product_image with content: {content}")
        if "product_image_id" not in content:
            response = generate_bad_request_response(
                "ProductImage ID is required to fetch product_image details."
            )
            return response
        status, product_image = ProductImage.get(content)
        if not status:
            response = generate_entity_not_found_response("ProductImage")
            return response
        logger.success(f"ProductImage fetched: {product_image}")
        response = generate_success_response("product_image fetched successfully")
        response["product_image"] = product_image
    except Exception as ex:
        logger.exception(f"Error in get_product_image: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_product_images(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all product_images with content: {content}")
        product_image_data, all_product_image_data = [], []
        _, all_product_image_data = ProductImage.get_all(content)
        if not all_product_image_data:
            response = generate_entity_not_found_response("ProductImages")
            return response
        for product_image in all_product_image_data:
            product_image_data.append(product_image.to_dict())
        logger.success(f"ProductImages fetched: {product_image_data}")
        response = generate_success_response("All product_images fetched successfully")
        response["product_image"] = product_image_data
    except Exception as ex:
        logger.exception(f"Error in get_all_product_images: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_product_image(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating product_image with content: {content}")
        updated_product_image = None
        content["product_image_id"] = content["product_image"].product_image_id
        status, product_image_data = ProductImage.get(content)
        if not status:
            response = generate_entity_not_found_response("ProductImage")
            return response
        product_image_data = ProductImage(**product_image_data)
        incoming_data = content["product_image"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                product_image_data.attributes = {**product_image_data.attributes, **value}
            else:
                setattr(product_image_data, key, value)
        product_image_data.modified_at = content["product_image"].modified_at
        status, updated_product_image = ProductImage.update(product_image_data)
        if not status:
            response = generate_not_acceptable_response("ProductImage update failed.")
            return response
        logger.success(f"ProductImage updated: {updated_product_image}")
        response = generate_success_response("product_image updated successfully")
        response["product_image"] = updated_product_image
    except Exception as ex:
        logger.exception(f"Error in update_product_image: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_product_image(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting product_image with content: {content}")
        if "product_image_id" not in content:
            response = generate_bad_request_response(
                "ProductImage ID is required to delete product_image."
            )
            return response
        status, product_image = ProductImage.get(content)
        if not status:
            response = generate_entity_not_found_response("ProductImage")
            return response
        product_image_data = ProductImage(**product_image)

        # for hard delete
        # status = ProductImage.delete(product_image_data)

        # for soft delete
        if "product_image" in content:
            product_image.deleted_by = content["product_image"].deleted_by
            product_image.deleted_at = content["product_image"].deleted_at
        elif "current_product_image" in content:
            product_image.deleted_by = content["current_product_image"].product_image_id
            product_image.deleted_at = get_current_time()
            status, _ = ProductImage.update(product_image_data)
        if not status:
            response = generate_not_acceptable_response("ProductImage deletion failed.")
            return response
        logger.success(f"ProductImage deleted: {product_image}")
        response = generate_success_response("product_image deleted successfully")
        response["product_image"] = product_image
    except Exception as ex:
        logger.exception(f"Error in delete_product_image: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_product_images(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total product_images with content: {content}")
        total_product_images, search_criteria = 0, []
        product_image_query = ProductImage.query
        columns = inspect(ProductImage).columns

        if not content.get("include_deleted"):
            product_image_query = product_image_query.filter(ProductImage.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(ProductImage, content["selected_column"], None)
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
        product_image_query = product_image_query.filter(or_(*search_criteria))
        total_product_images = product_image_query.count()
        logger.success(f"Total product_images fetched: {total_product_images}")
        response = generate_success_response("Total product_images fetched successfully")
        response["total_product_images"] = total_product_images
    except Exception as ex:
        logger.exception(f"Error in get_total_product_images: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_product_images(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited product_images with content: {content}")
        product_images_data, product_images, columns_list = [], None, None
        product_image_query = ProductImage.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(ProductImage).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            product_image_query = product_image_query.filter(ProductImage.deleted_by.is_(None))
        product_images = (
            product_image_query.order_by(desc(ProductImage.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for product_image in product_images:
            product_images_data.append(product_image.to_dict())
        logger.success(f"ProductImages fetched: {product_images_data}")
        response = generate_success_response("Limited product_images fetched successfully")
        response["records"] = product_images_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_product_images: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_product_images(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered product_images with content: {content}")
        product_images_data, product_images, columns_list, search_criteria = [], [], None, []
        product_image_query = ProductImage.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(ProductImage).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(ProductImage, content["selected_column"], None)
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
        product_image_query = product_image_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            product_image_query = product_image_query.filter(ProductImage.deleted_by.is_(None))
        product_images = (
            product_image_query.order_by(desc(ProductImage.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for product_image in product_images:
            product_images_data.append(product_image.to_dict())

        logger.success(f"ProductImages fetched: {product_images_data}")
        response = generate_success_response("Filtered product_images fetched successfully")
        response["records"] = product_images_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_product_images: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

from utils.constants import DEFAULT_API_RESPONSE_OBJ
from management.entities.review.model import Review
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


def create_review(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Creating review with content: {content}")
        if "review" not in content:
            response = generate_bad_request_response(
                "Review data is required to create a review."
            )
            return response
        review = Review(**content["review"].model_dump())
        status, review_data = Review.add(review)
        if not status:
            response = generate_not_acceptable_response("Review creation failed.")
            return response
        response = generate_success_response("review created successfully")
        logger.success(f"Review created: {review_data}")
        response["review"] = review_data.to_dict()
    except Exception as ex:
        logger.exception(f"Error in create_review: {ex}")
    return response


def get_review(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching review with content: {content}")
        if "review_id" not in content:
            response = generate_bad_request_response(
                "Review ID is required to fetch review details."
            )
            return response
        status, review = Review.get(content)
        if not status:
            response = generate_entity_not_found_response("Review")
            return response
        logger.success(f"Review fetched: {review}")
        response = generate_success_response("review fetched successfully")
        response["review"] = review
    except Exception as ex:
        logger.exception(f"Error in get_review: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_all_reviews(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching all reviews with content: {content}")
        review_data, all_review_data = [], []
        _, all_review_data = Review.get_all(content)
        if not all_review_data:
            response = generate_entity_not_found_response("Reviews")
            return response
        for review in all_review_data:
            review_data.append(review.to_dict())
        logger.success(f"Reviews fetched: {review_data}")
        response = generate_success_response("All reviews fetched successfully")
        response["review"] = review_data
    except Exception as ex:
        logger.exception(f"Error in get_all_reviews: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def update_review(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Updating review with content: {content}")
        updated_review = None
        content["review_id"] = content["review"].review_id
        status, review_data = Review.get(content)
        if not status:
            response = generate_entity_not_found_response("Review")
            return response
        review_data = Review(**review_data)
        incoming_data = content["review"].model_dump(exclude_unset=True)
        for key, value in incoming_data.items():
            if key == "attributes":
                review_data.attributes = {**review_data.attributes, **value}
            else:
                setattr(review_data, key, value)
        review_data.modified_at = content["review"].modified_at
        status, updated_review = Review.update(review_data)
        if not status:
            response = generate_not_acceptable_response("Review update failed.")
            return response
        logger.success(f"Review updated: {updated_review}")
        response = generate_success_response("review updated successfully")
        response["review"] = updated_review
    except Exception as ex:
        logger.exception(f"Error in update_review: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def delete_review(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Deleting review with content: {content}")
        if "review_id" not in content:
            response = generate_bad_request_response(
                "Review ID is required to delete review."
            )
            return response
        status, review = Review.get(content)
        if not status:
            response = generate_entity_not_found_response("Review")
            return response
        review_data = Review(**review)

        # for hard delete
        # status = Review.delete(review_data)

        # for soft delete
        if "review" in content:
            review.deleted_by = content["review"].deleted_by
            review.deleted_at = content["review"].deleted_at
        elif "current_review" in content:
            review.deleted_by = content["current_review"].review_id
            review.deleted_at = get_current_time()
            status, _ = Review.update(review_data)
        if not status:
            response = generate_not_acceptable_response("Review deletion failed.")
            return response
        logger.success(f"Review deleted: {review}")
        response = generate_success_response("review deleted successfully")
        response["review"] = review
    except Exception as ex:
        logger.exception(f"Error in delete_review: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_total_reviews(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching total reviews with content: {content}")
        total_reviews, search_criteria = 0, []
        review_query = Review.query
        columns = inspect(Review).columns

        if not content.get("include_deleted"):
            review_query = review_query.filter(Review.deleted_by.is_(None))
        params = extract_query_params(content)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        if search_string:
            if selected_column:
                selected_column = getattr(Review, content["selected_column"], None)
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
        review_query = review_query.filter(or_(*search_criteria))
        total_reviews = review_query.count()
        logger.success(f"Total reviews fetched: {total_reviews}")
        response = generate_success_response("Total reviews fetched successfully")
        response["total_reviews"] = total_reviews
    except Exception as ex:
        logger.exception(f"Error in get_total_reviews: {ex}")
        respomse = generate_internal_server_error_response(str(ex))
    return response


def get_limited_reviews(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching limited reviews with content: {content}")
        reviews_data, reviews, columns_list = [], None, None
        review_query = Review.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)

        columns = inspect(Review).columns
        columns_list = [column.name for column in columns]
        if not content.get("include_deleted"):
            review_query = review_query.filter(Review.deleted_by.is_(None))
        reviews = (
            review_query.order_by(desc(Review.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )

        for review in reviews:
            reviews_data.append(review.to_dict())
        logger.success(f"Reviews fetched: {reviews_data}")
        response = generate_success_response("Limited reviews fetched successfully")
        response["records"] = reviews_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_limited_reviews: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response


def get_filtered_reviews(content):
    response = DEFAULT_API_RESPONSE_OBJ.copy()
    try:
        logger.debug(f"Fetching filtered reviews with content: {content}")
        reviews_data, reviews, columns_list, search_criteria = [], [], None, []
        review_query = Review.query

        params = extract_query_params(content)
        skip = params.get("skip", 0)
        limit = params.get("limit", 10)
        search_string = params.get("search_string", "")
        selected_column = params.get("selected_column", "")

        columns = inspect(Review).columns
        columns_list = [column.name for column in columns]

        if search_string:
            if selected_column:
                selected_column = getattr(Review, content["selected_column"], None)
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
        review_query = review_query.filter(or_(*search_criteria))
        if not content.get("include_deleted"):
            review_query = review_query.filter(Review.deleted_by.is_(None))
        reviews = (
            review_query.order_by(desc(Review.created_at))
            .offset(int(skip))
            .limit(int(limit))
            .all()
        )
        for review in reviews:
            reviews_data.append(review.to_dict())

        logger.success(f"Reviews fetched: {reviews_data}")
        response = generate_success_response("Filtered reviews fetched successfully")
        response["records"] = reviews_data
        response["columns_list"] = columns_list
    except Exception as ex:
        logger.exception(f"Error in get_filtered_reviews: {ex}")
        response = generate_internal_server_error_response(str(ex))
    return response

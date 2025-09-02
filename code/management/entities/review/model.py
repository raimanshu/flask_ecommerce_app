from infra.database import db
from flask import jsonify
from utils.constants import DB_COLUMN_MAX_LENGTH
from sqlalchemy.exc import SQLAlchemyError
from infra.logging import logger


class Review(db.Model):
    __tablename__ = "review"

    review_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), primary_key=True)
    user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("user.user_id"), nullable=False)
    product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), db.ForeignKey("product.product_id"), nullable=False)
    # user_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    # product_id = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    attributes = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=False)
    modified_at = db.Column(
        db.DateTime,
        nullable=True,
    )
    modified_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(DB_COLUMN_MAX_LENGTH), nullable=True)

    def to_dict(self):
        return {
            "review_id": self.review_id,
            "user_id": self.revieuser_idwname,
            "product_id": self.product_id,
            "rating": self.rating,
            "comment": self.comment,
            "attributes": self.attributes,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "modified_at": self.modified_at if self.modified_at else None,
            "modified_by": self.modified_by,
            "deleted_at": self.deleted_at if self.deleted_at else None,
            "deleted_by": self.deleted_by,
        }

    def add(self):
        try:
            logger.debug(f"Adding review: {self} to review table")
            return _add_review(self)
        except Exception as e:
            logger.exception(f"Error adding review: {e}")
            return False, None

    def update(self):
        try:
            logger.debug(f"Updating review: {self} to review table")
            return _update_review(self)
        except Exception as e:
            logger.exception(f"Error updating review: {e}")
            return False, None

    def delete(review):
        try:
            logger.debug(f"Deleting review: {review} from review table")
            return _delete_review(review)
        except Exception as e:
            logger.exception(f"Error deleting review: {e}")
            return False, None

    @staticmethod
    def get(content):
        try:
            logger.debug(f"Fetching review: {content} from review table")
            return _get_review(content)
        except Exception as ex:
            logger.exception(f"Error fetching review: {ex}")
            return False, None

    @staticmethod
    def get_all(content):
        try:
            logger.debug(f"Fetching all reviews from review table")
            return _get_all_reviews(content)
        except Exception as ex:
            logger.exception(f"Error fetching all reviews: {ex}")
            return False, None


class ReviewProvider(Review):
    @staticmethod
    def get_by_attribute(attribute_name, content):

        try:
            logger.debug(f"Fetching review by attribute {attribute_name}: {content}")
            return _get_review_by_attribute(attribute_name, content)
        except Exception:
            logger.exception(
                f"Critical error in ReviewProvider.get_by_attribute - {content}"
            )
            return False, None

    @staticmethod
    def get_collective_data_by_attribute(attribute_name, content, require_object=False):
        try:
            logger.debug(
                f"Fetching collective data by attribute {attribute_name}: {content}"
            )
            return _get_collective_review_by_attribute(
                attribute_name, content, require_object
            )
        except Exception:
            logger.exception(
                f"Critical error in ReviewProvider.get_collective_data_by_attribute - {content}"
            )
            return False, None


# region Review Helper Functions


def _get_review(content):
    try:
        logger.debug(f"Fetching review: {content}")
        if content.get("review", ""):
            content["review_id"] = content["review"].review_id
        elif content.get("entity_id", ""):
            content["review_id"] = content["entity_id"]
        review = None
        # review = Review.query.filter_by(review_id=content["review_id"]).first()
        review_query = db.session.query(Review).filter_by(
            review_id=content["review_id"]
        )
        if not content.get("include_deleted"):
            review_query = review_query.filter(Review.deleted_by.is_(None))
        review = review_query.first()
        if not review:
            logger.debug("Review not found")
            return False, None
        review_dict = review.to_dict()
        logger.success(f"Review fetched: {review_dict}")
        return True, review_dict
    except Exception as ex:
        logger.exception(f"Error fetching review: {ex}")
        raise ex


def _get_all_reviews(content):
    try:
        logger.debug(f"Fetching all reviews: {content}")
        review = None
        # review = Review.query.all()
        review_query = db.session.query(Review)
        if not content.get("include_deleted"):
            review_query = review_query.filter(Review.deleted_by.is_(None))
        review = review_query.all()
        if not review:
            logger.debug("No reviews found")
            return False, None
        logger.success(f"Reviews fetched: {review}")
        return True, review
    except Exception as ex:
        logger.exception(f"Error fetching all reviews: {ex}")
        raise ex


def _delete_review(review):
    try:
        logger.debug(f"Deleting review: {review}")
        # Review.query.filter_by(review_id=review.review_id).delete()
        db.session.query(Review).filter_by(review_id=review.review_id).delete()
        db.session.commit()
        logger.success(f"Review deleted: {review}")
        return True
    except SQLAlchemyError as ex:
        logger.exception(f"Error deleting review: {ex}")
        db.session.rollback()
        return ex


def _add_review(review):
    try:
        logger.debug(f"Adding review: {review}")
        db.session.add(review)
        db.session.commit()
        db.session.refresh(review)
        review_dict = review.to_dict()
        logger.success(f"Review added: {review_dict}")
        return True, review
    except SQLAlchemyError as ex:
        logger.exception(f"Error adding review: {ex}")
        db.session.rollback()
        raise ex


def _update_review(review):
    try:
        logger.debug(f"Updating review: {review}")
        updated_review = None
        # Review.query.filter_by(review_id=review.review_id).update(review.to_dict())
        updated_review = db.session.merge(review)
        db.session.commit()
        if not updated_review:
            logger.exception("Review not updated")
            return False, None
        updated_review_dict = updated_review.to_dict()
        logger.success(f"Review updated: {updated_review_dict}")
        return True, updated_review_dict
    except Exception as ex:
        logger.exception(f"Error updating review: {ex}")
        db.session.rollback()
        raise ex


# endregion


# region ReviewProvider Helper Functions
def _get_review_by_attribute(attribute_name, content):
    try:
        logger.debug(f"Fetching review by attribute {attribute_name}: {content}")
        review = None
        review_query = db.session.query(Review).filter(
            getattr(Review, attribute_name) == content.get(f"{attribute_name}", "")
        )
        if not content.get("include_deleted", False):
            review_query = review_query.filter(Review.deleted_by.is_(None))
        review = review_query.first()
        if not review:
            logger.debug(
                f"No review found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        review_dict = review.to_dict()
        logger.success(f"Review fetched by attribute {attribute_name}: {review_dict}")
        return True, review
    except Exception as ex:
        logger.exception(f"Error fetching review by attribute {attribute_name}: {ex}")
        raise ex


def _get_collective_review_by_attribute(attribute_name, content, require_object):
    try:
        logger.debug(
            f"Fetching collective review data by attribute {attribute_name}: {content}"
        )
        reviews_dict = None
        reviews = (
            db.session.query(Review)
            .filter(
                getattr(Review, attribute_name).in_(
                    content.get(f"{attribute_name}", [])
                )
            )
            .all()
        )
        if require_object:
            reviews_dict = {
                getattr(review_data, attribute_name): review_data
                for review_data in reviews
            }
        else:
            reviews_dict = {
                getattr(review_data, attribute_name): review_data.to_dict()
                for review_data in reviews
            }
        if not reviews_dict:
            logger.debug(
                f"No reviews found with {attribute_name} in {content.get(f'{attribute_name}', '')}"
            )
            return False, None
        logger.success(f"Reviews fetched by attribute {attribute_name}: {reviews_dict}")
        return True, reviews_dict
    except Exception as ex:
        logger.exception(
            f"Error fetching collective review data by attribute {attribute_name}: {ex}"
        )
        raise ex


# endregion

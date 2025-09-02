
from management.entities.user.apis import (
    create_user,
    get_user,
    get_all_users,
    update_user,
    delete_user,
    get_total_users,
    get_limited_users,
    get_filtered_users,
)
from management.entities.user.schema import UserCreate, UserUpdate






ENTITY_API_ROUTES = {
    "user": {
        "create": {"schema": UserCreate, "api": create_user},
        "fetch": {"schema": "", "api": get_user},
        "fetch_all": {"schema": "", "api": get_all_users},
        "update": {"schema": UserUpdate, "api": update_user},
        "delete": {"schema": "", "api": delete_user},
        "total": {"schema": "", "api": get_total_users},
        "get_limited_records": {"schema": "", "api": get_limited_users},
        "get_filtered_records": {"schema": "", "api": get_filtered_users},


        # "create": {"schema": UserCreate, "api": create_user},
        # "fetch": {"schema": "", "api": get_user},
        # "fetch_all": {"schema": "", "api": get_all_users},
        # "update": {"schema": UserUpdate, "api": update_user},
        # "delete": {"schema": UserDelete, "api": delete_user},
        # "total": {"schema": "", "api": get_total_users},
        # "get_limited_records": {"schema": "", "api": get_limited_users},
        # "get_filtered_records": {"schema": "", "api": get_filtered_users},
    },
    "product": {
        # "create": {"schema": UserCreate, "api": create_user},
        # "fetch": {"schema": "", "api": get_user},
        # "fetch_all": {"schema": "", "api": get_all_users},
        # "update": {"schema": UserUpdate, "api": update_user},
        # "delete": {"schema": UserDelete, "api": delete_user},
        # "total": {"schema": "", "api": get_total_users},
        # "get_limited_records": {"schema": "", "api": get_limited_users},
        # "get_filtered_records": {"schema": "", "api": get_filtered_users},
    },
}

AUTHENTICATION_API_ROUTES = {
    "login": user_login,
    "logout": user_logout,
    # "get-user-otp": get_user_otp,
    # "verify-user-otp": verify_user_otp,
    # "forgot-user-password": forgot_user_password,
    # "validate-user-token": validate_user_token,
    # "reset-user-password": reset_user_password,
}

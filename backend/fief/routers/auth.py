from fief.fastapi_users import bearer_token_backend, fastapi_users

router = fastapi_users.get_auth_router(bearer_token_backend)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fief.routers.accounts import router as accounts_router
from fief.routers.auth import router as auth_router
from fief.routers.register import router as register_router
from fief.settings import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(accounts_router, prefix="/accounts")
app.include_router(auth_router, prefix="/auth")
app.include_router(register_router, prefix="/auth")

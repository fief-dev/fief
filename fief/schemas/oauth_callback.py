from pydantic import BaseModel


class CallBackBody(BaseModel):
    code: str | None = None
    state: str | None = None

    @classmethod
    def get_callback_body(cls, callback_body: str):
        parsed_callback_body = callback_body.split("&")
        return cls.model_validate(
            {
                key: value
                for key, value in (item.split("=") for item in parsed_callback_body)
            }
        )

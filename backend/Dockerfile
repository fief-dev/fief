FROM python:alpine3.10

WORKDIR /app

COPY requirements.txt .

RUN apk update && apk add --no-cache build-base libffi-dev postgresql-dev && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

ENV PORT=80
EXPOSE ${PORT}

CMD [ "gunicorn", "-k uvicorn.workers.UvicornWorker", "fief.app:app" ]

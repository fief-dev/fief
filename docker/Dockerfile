FROM python:3.10-alpine

ARG FIEF_VERSION
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apk update \
    && apk add --virtual build-deps build-base \
    && apk add --no-cache libffi-dev postgresql-dev mariadb-dev redis \
    && pip install --upgrade pip supervisor \
    && python --version \
    && pip install fief-server==${FIEF_VERSION} \
    && apk del build-deps && \
    mkdir -p /data/db

COPY supervisord.conf /etc/supervisord.conf

ENV DATABASE_LOCATION=/data/db

ENV PORT=8000
EXPOSE ${PORT}

CMD ["supervisord", "-c", "/etc/supervisord.conf"]

FROM python:3.10-alpine

ARG FIEF_VERSION

WORKDIR /app

RUN apk update \
    && apk add --virtual build-deps build-base \
    && apk add --no-cache libffi-dev postgresql-dev mariadb-dev redis supervisor \
    && pip install --upgrade pip \
    && python --version \
    && pip install fief-server==${FIEF_VERSION} \
    && apk del build-deps && \
    mkdir -p /data/db

COPY supervisord.conf /etc/supervisord.conf

ENV DATABASE_LOCATION=/data/db

ENV PORT=8000
EXPOSE ${PORT}

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]

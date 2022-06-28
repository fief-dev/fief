FROM python:3.10-slim

ARG FIEF_VERSION
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential redis libpq-dev \
    && pip install --upgrade pip supervisor \
    && python --version \
    && pip install fief-server==${FIEF_VERSION} \
    && apt-get autoremove -y build-essential \
    && mkdir -p /data/db

COPY supervisord.conf /etc/supervisord.conf

ENV DATABASE_LOCATION=/data/db

ENV PORT=8000
EXPOSE ${PORT}

CMD ["supervisord", "-c", "/etc/supervisord.conf"]

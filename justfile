default:
  @just --list

compose command:
  docker-compose -f docker-compose.yml -f docker-compose.dev.yml {{command}}

start:
  just compose "up -d --build"

stop:
  just compose "stop"

migrate-global-db:
  just compose "run backend alembic -n global upgrade head"

migrate-account-db:
  just compose "run backend alembic -n global upgrade head"

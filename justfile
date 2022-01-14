default:
  @just --list

compose command:
  docker-compose -f docker-compose.yml -f docker-compose.dev.yml {{command}}

start:
  just compose "up -d --build"

restart:
  just compose "restart"

stop:
  just compose "stop"

revision-global-db message:
  just compose "exec backend alembic -n global revision --autogenerate -m \"{{message}}\""

migrate-global-db:
  just compose "exec backend alembic -n global upgrade head"

revision-account-db message:
  just compose "exec backend alembic -n account revision --autogenerate -m \"{{message}}\""

migrate-account-db:
  just compose "exec backend alembic -n account upgrade head"

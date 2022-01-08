default:
  @just --list

compose command:
  docker-compose -f docker-compose.yml -f docker-compose.dev.yml {{command}}

start:
  just compose "up -d --build"

stop:
  just compose "stop"

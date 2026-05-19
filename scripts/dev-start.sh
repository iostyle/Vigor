#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT_DIR/vigor-server"
CLIENT_DIR="$ROOT_DIR/vigor-client"
RUNTIME_DIR="$ROOT_DIR/.vigor-dev"
LOG_DIR="$RUNTIME_DIR/logs"
PID_DIR="$RUNTIME_DIR/pids"

API_PORT="${API_PORT:-8000}"
CLIENT_PORT="${CLIENT_PORT:-3000}"
API_HOST="${API_HOST:-0.0.0.0}"
CLIENT_HOST="${CLIENT_HOST:-0.0.0.0}"

info() {
  printf '\033[1;34m[info]\033[0m %s\n' "$*"
}

warn() {
  printf '\033[1;33m[warn]\033[0m %s\n' "$*"
}

fail() {
  printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "缺少命令: $1"
}

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    printf 'docker compose'
  elif command -v docker-compose >/dev/null 2>&1; then
    printf 'docker-compose'
  else
    fail "缺少 Docker Compose: 请安装 Docker Desktop 或 docker-compose"
  fi
}

read_env_value() {
  local file="$1"
  local key="$2"
  if [[ ! -f "$file" ]]; then
    return 1
  fi
  grep -E "^${key}=" "$file" | tail -n 1 | cut -d '=' -f 2-
}

write_or_replace_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  if grep -qE "^${key}=" "$file"; then
    tmp_file="$(mktemp)"
    sed "s|^${key}=.*|${key}=${value}|" "$file" >"$tmp_file"
    mv "$tmp_file" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >>"$file"
  fi
}

ensure_env_files() {
  if [[ ! -f "$SERVER_DIR/.env" ]]; then
    cp "$SERVER_DIR/.env.example" "$SERVER_DIR/.env"
    info "已创建 vigor-server/.env"
  fi

  local client_env="$CLIENT_DIR/.env.local"
  if [[ ! -f "$client_env" ]]; then
    cp "$CLIENT_DIR/.env.example" "$client_env"
    info "已创建 vigor-client/.env.local"
  fi

  local api_key
  api_key="$(read_env_value "$SERVER_DIR/.env" "API_KEY" || true)"
  if [[ -n "$api_key" ]]; then
    write_or_replace_env_value "$client_env" "VITE_API_KEY" "$api_key"
  fi

  write_or_replace_env_value "$client_env" "VITE_API_BASE_URL" "http://localhost:${API_PORT}"
}

is_pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

ensure_port_available() {
  local port="$1"
  local name="$2"
  local pid_file="$PID_DIR/${name}.pid"
  if [[ -f "$pid_file" ]]; then
    local existing_pid
    existing_pid="$(cat "$pid_file")"
    if is_pid_alive "$existing_pid"; then
      return
    fi
  fi

  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    fail "端口 ${port} 已被占用。请先释放端口,或设置 API_PORT/CLIENT_PORT 后重试。"
  fi
}

start_process() {
  local name="$1"
  local workdir="$2"
  local command="$3"
  local pid_file="$PID_DIR/${name}.pid"
  local log_file="$LOG_DIR/${name}.log"

  if [[ -f "$pid_file" ]]; then
    local existing_pid
    existing_pid="$(cat "$pid_file")"
    if is_pid_alive "$existing_pid"; then
      info "${name} 已在运行 (PID ${existing_pid})"
      return
    fi
    rm -f "$pid_file"
  fi

  info "启动 ${name}"
  (
    cd "$workdir"
    nohup bash -lc "$command" >"$log_file" 2>&1 &
    printf '%s' "$!" >"$pid_file"
  )
}

wait_for_http() {
  local url="$1"
  local name="$2"
  local attempts="${3:-30}"

  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      info "${name} 已就绪"
      return
    fi
    sleep 1
  done

  fail "${name} 启动超时,请查看 $LOG_DIR"
}

main() {
  require_command docker
  require_command poetry
  require_command npm
  require_command curl
  require_command lsof

  mkdir -p "$LOG_DIR" "$PID_DIR"

  ensure_env_files

  ensure_port_available "$API_PORT" "api"
  ensure_port_available "$CLIENT_PORT" "client"

  local compose
  compose="$(compose_cmd)"

  info "启动 PostgreSQL 和 Redis"
  (
    cd "$SERVER_DIR"
    $compose up -d postgres redis
  )

  info "安装后端依赖"
  (
    cd "$SERVER_DIR"
    poetry install
  )

  info "安装前端依赖"
  (
    cd "$CLIENT_DIR"
    npm install
  )

  info "执行数据库迁移"
  (
    cd "$SERVER_DIR"
    poetry run alembic upgrade head
  )

  start_process "api" "$SERVER_DIR" "poetry run uvicorn app.main:app --host ${API_HOST} --port ${API_PORT}"
  wait_for_http "http://127.0.0.1:${API_PORT}/docs" "后端 API"

  start_process "celery-worker" "$SERVER_DIR" "poetry run celery -A app.celery_app worker -n vigor-worker@%h -Q crawler,processor,updater --loglevel=info"
  start_process "celery-beat" "$SERVER_DIR" "poetry run celery -A app.celery_app beat --loglevel=info --schedule '$RUNTIME_DIR/celerybeat-schedule.db'"
  start_process "client" "$CLIENT_DIR" "npm run dev -- --host ${CLIENT_HOST} --port ${CLIENT_PORT}"

  cat <<EOF

Vigor 开发环境已启动

前台/后台: http://localhost:${CLIENT_PORT}
API 文档:  http://localhost:${API_PORT}/docs
运行日志:  $LOG_DIR

停止本地进程:
  ./scripts/dev-stop.sh

停止数据库和 Redis:
  cd vigor-server && $compose stop postgres redis

EOF
}

main "$@"

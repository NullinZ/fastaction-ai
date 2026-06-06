#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5177}"
FASTACTION_INSTALL_DEPS="${FASTACTION_INSTALL_DEPS:-1}"

MODE="${1:-all}"
BACKEND_PID=""

usage() {
  cat <<'USAGE'
Usage: scripts/start_dev.sh [all|backend|frontend]

Environment:
  PYTHON_BIN                 Python executable, default: python3
  BACKEND_HOST               Backend host, default: 127.0.0.1
  BACKEND_PORT               Backend port, default: 8000
  FRONTEND_HOST              Frontend host, default: 127.0.0.1
  FRONTEND_PORT              Frontend port, default: 5177
  FASTACTION_INSTALL_DEPS    Install missing deps before start, default: 1
USAGE
}

cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
    wait "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
}

ensure_python_env() {
  cd "${ROOT_DIR}"
  if [[ ! -d ".venv" ]]; then
    "${PYTHON_BIN}" -m venv .venv
  fi
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.venv/bin/activate"
  if [[ "${FASTACTION_INSTALL_DEPS}" != "0" ]]; then
    python -m pip install -e ".[server]"
  fi
}

ensure_frontend_env() {
  cd "${ROOT_DIR}/frontend/workbench"
  if [[ "${FASTACTION_INSTALL_DEPS}" != "0" && ! -d "node_modules" ]]; then
    npm install
  fi
}

start_backend() {
  ensure_python_env
  cd "${ROOT_DIR}"
  export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
  python -m uvicorn scripts.dev_app:app \
    --host "${BACKEND_HOST}" \
    --port "${BACKEND_PORT}" \
    --reload
}

start_frontend() {
  ensure_frontend_env
  cd "${ROOT_DIR}/frontend/workbench"
  FASTACTION_API_BASE_URL="http://${BACKEND_HOST}:${BACKEND_PORT}" \
    npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}"
}

case "${MODE}" in
  all)
    trap cleanup EXIT INT TERM
    start_backend &
    BACKEND_PID="$!"
    start_frontend
    ;;
  backend)
    start_backend
    ;;
  frontend)
    start_frontend
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 2
    ;;
esac

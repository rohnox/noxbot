#!/usr/bin/env bash
set -euo pipefail

# ---------- Config (you can override via env) ----------
REPO_URL="${REPO_URL:-https://github.com/rohnox/noxbot.git}"
APP_DIR="${APP_DIR:-$HOME/noxbot}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BRANCH="${BRANCH:-main}"
START_ON_INSTALL="${START_ON_INSTALL:-1}"   # 1=start after install, 0=skip
# ------------------------------------------------------

log() { printf "\033[1;32m[+] %s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m[!] %s\033[0m\n" "$*"; }
err() { printf "\033[1;31m[!] %s\033[0m\n" "$*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || return 1
}

install_system_deps() {
  if need_cmd apt-get; then
    warn "Installing system deps with apt-get (sudo may be required)..."
    if need_cmd sudo; then SUDO="sudo"; else SUDO=""; fi
    $SUDO apt-get update -y
    $SUDO apt-get install -y git $PYTHON_BIN $PYTHON_BIN-venv python3-pip sqlite3
  else
    warn "apt-get not found; please ensure git, python3, venv and sqlite3 are installed."
  fi
}

clone_or_update_repo() {
  if [ -d "$APP_DIR/.git" ]; then
    log "Repo exists at $APP_DIR — pulling latest..."
    git -C "$APP_DIR" fetch --all --quiet
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only
  else
    log "Cloning \"$REPO_URL\" into $APP_DIR ..."
    git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  fi
}

create_venv_and_install() {
  log "Creating venv and installing requirements..."
  cd "$APP_DIR"
  if [ ! -d ".venv" ]; then
    $PYTHON_BIN -m venv .venv
  fi
  . .venv/bin/activate
  python -m pip install --upgrade pip wheel
  pip install -r requirements.txt
}

ensure_env() {
  cd "$APP_DIR"
  if [ ! -f ".env" ]; then
    log "Creating .env from .env.example"
    if [ -f ".env.example" ]; then
      cp .env.example .env
    else
      touch .env
      echo "BOT_TOKEN=" >> .env
      echo "ADMINS=" >> .env
    fi
  fi

  # Read current values
  CUR_TOKEN="$(grep -E '^BOT_TOKEN=' .env || true)"
  CUR_ADMINS="$(grep -E '^ADMINS=' .env || true)"

  if [ -z "${BOT_TOKEN:-}" ]; then
    if [ -z "$CUR_TOKEN" ]; then
      read -rp "Enter your BOT_TOKEN: " BOT_TOKEN
    else
      warn "BOT_TOKEN already present in .env (skipping prompt). To change later, edit $APP_DIR/.env"
    fi
  fi
  if [ -z "${ADMINS:-}" ]; then
    if [ -z "$CUR_ADMINS" ]; then
      read -rp "Enter admin numeric IDs (comma-separated): " ADMINS
    else
      warn "ADMINS already present in .env (skipping prompt). To change later, edit $APP_DIR/.env"
    fi
  fi

  # Write values if provided via env or prompt
  if [ -n "${BOT_TOKEN:-}" ]; then
    if grep -q '^BOT_TOKEN=' .env; then
      sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=${BOT_TOKEN}|g" .env
    else
      echo "BOT_TOKEN=${BOT_TOKEN}" >> .env
    fi
  fi
  if [ -n "${ADMINS:-}" ]; then
    if grep -q '^ADMINS=' .env; then
      sed -i "s|^ADMINS=.*|ADMINS=${ADMINS}|g" .env
    else
      echo "ADMINS=${ADMINS}" >> .env
    fi
  fi

  # Payment/domain not needed for test; leave others as defaults.
}

install_run_helper() {
  cd "$APP_DIR"
  cat > run.sh <<'RSCRIPT'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV="${APP_DIR}/.venv"
LOG_DIR="${APP_DIR}/logs"
PID_FILE="${APP_DIR}/.bot.pid"

PY="${VENV}/bin/python"

mkdir -p "$LOG_DIR"

start() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Bot already running (PID $(cat "$PID_FILE"))"
    exit 0
  fi
  nohup "$PY" -m app.run_polling \
    >> "${LOG_DIR}/bot.out.log" 2>> "${LOG_DIR}/bot.err.log" &
  echo $! > "$PID_FILE"
  echo "Bot started (PID $(cat "$PID_FILE"))"
}

stop() {
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID" || true
      sleep 1
      if kill -0 "$PID" 2>/dev/null; then
        kill -9 "$PID" || true
      fi
    fi
    rm -f "$PID_FILE"
    echo "Bot stopped"
  else
    echo "Bot not running"
  fi
}

status() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Bot: RUNNING (PID $(cat "$PID_FILE"))"
  else
    echo "Bot: STOPPED"
  fi
}

logs() {
  echo "=== tail -n 50 logs/bot.out.log ==="
  tail -n 50 "${LOG_DIR}/bot.out.log" 2>/dev/null || true
  echo
  echo "=== tail -n 50 logs/bot.err.log ==="
  tail -n 50 "${LOG_DIR}/bot.err.log" 2>/dev/null || true
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  logs) logs ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs}"
    ;;
esac
RSCRIPT
  chmod +x run.sh
}

start_bot() {
  cd "$APP_DIR"
  . .venv/bin/activate
  ./run.sh start
}

main() {
  install_system_deps || true
  clone_or_update_repo
  create_venv_and_install
  ensure_env
  install_run_helper
  if [ "${START_ON_INSTALL}" = "1" ]; then
    start_bot
    log "Done. Use: $APP_DIR/run.sh {status|logs|stop}"
  else
    warn "Skip start. You can start later with: $APP_DIR/run.sh start"
  fi
}

main "$@"

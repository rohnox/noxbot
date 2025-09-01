#!/usr/bin/env bash
set -euo pipefail

# ============================================
# tele-premium-stars-bot — Turnkey Installer
# ============================================
# This script installs Docker & Compose (if needed),
# clones your repo, prepares .env, brings up services,
# initializes the DB, and (optionally) sets up Nginx + SSL.
#
# Usage:
#   chmod +x install_telebot.sh
#   ./install_telebot.sh \
#     REPO_URL=https://github.com/<user>/<repo>.git \
#     APP_DIR=/opt/telebot \
#     BRANCH=main \
#     START_ON_INSTALL=1 \
#     WITH_NGINX=0 \
#     DOMAIN=admin.example.com \
#     CERTBOT_EMAIL=me@example.com
#
# Env vars:
#   REPO_URL           (required) Git repo URL containing docker-compose.yaml
#   APP_DIR            (default: $HOME/tele-premium-stars-bot)
#   BRANCH             (default: main)
#   START_ON_INSTALL   (default: 1) 1=start right away, 0=skip
#   WITH_NGINX         (default: 0) 1=configure Nginx reverse proxy
#   DOMAIN             (opt) domain for admin web (used if WITH_NGINX=1)
#   CERTBOT_EMAIL      (opt) email for Let's Encrypt (used if WITH_NGINX=1)
#   ADMIN_PORT         (default: 8080) internal admin service port
#
# App .env values (will prompt if missing in .env):
#   BOT_TOKEN
#   ADMIN_ALLOWED_IDS
#   CURRENCY (default IRR)
#   TZ (default Asia/Tehran)
#
# Notes:
# - Make sure your DNS for DOMAIN points to this VPS before enabling SSL.
# - Script is idempotent; safe to re-run.
# ============================================

# ------------- Config -------------
: "${APP_DIR:="$HOME/tele-premium-stars-bot"}"
: "${BRANCH:="main"}"
: "${START_ON_INSTALL:="1"}"
: "${WITH_NGINX:="0"}"
: "${DOMAIN:=""}"
: "${CERTBOT_EMAIL:=""}"
: "${ADMIN_PORT:="8080"}"
: "${REPO_URL:="https://github.com/rohnox/noxbot.git"}"

log()  { printf "\033[1;32m[+] %s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m[!] %s\033[0m\n" "$*"; }
err()  { printf "\033[1;31m[✗] %s\033[0m\n" "$*"; }

need_cmd() { command -v "$1" >/dev/null 2>&1; }

require() {
  if ! need_cmd "$1"; then
    err "Missing required command: $1"
    exit 1
  fi
}

ask() {
  local prompt="$1" var="$2" def="${3:-}"
  local ans
  if [ -n "${!var:-}" ]; then
    return 0
  fi
  if [ -n "$def" ]; then
    read -rp "$prompt [$def]: " ans || true
    ans="${ans:-$def}"
  else
    read -rp "$prompt: " ans || true
  fi
  export "$var"="$ans"
}

require_repo_url() {
  if [ -z "$REPO_URL" ]; then
    err "REPO_URL is required. Example: REPO_URL=https://github.com/<user>/<repo>.git"
    exit 1
  fi
}

install_prereqs() {
  if need_cmd apt-get; then
    log "Installing prerequisites via apt-get (sudo may be required)…"
    if need_cmd sudo; then SUDO="sudo"; else SUDO=""; fi
    $SUDO apt-get update -y
    $SUDO apt-get install -y \
      git curl ca-certificates gnupg lsb-release ufw
  else
    warn "apt-get not found (non-Ubuntu/Debian?). Ensure git, curl, ufw installed."
  fi
}

install_docker() {
  if need_cmd docker && need_cmd docker compose; then
    log "Docker & Compose already installed."
    return 0
  fi

  if need_cmd apt-get; then
    log "Installing Docker Engine & Compose plugin…"
    if need_cmd sudo; then SUDO="sudo"; else SUDO=""; fi
    $SUDO install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu $(. /etc/os-release; echo $VERSION_CODENAME) stable" \
      | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
    $SUDO apt-get update -y
    $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    if groups "$USER" | grep -qv '\bdocker\b'; then
      $SUDO usermod -aG docker "$USER" || true
      warn "User \"$USER\" added to docker group. You may need to logout/login for group to take effect."
    fi
  else
    err "Automatic Docker install not supported on this distro. Install Docker manually and re-run."
    exit 1
  fi
}

clone_or_update_repo() {
  if [ -d "$APP_DIR/.git" ]; then
    log "Repo exists at $APP_DIR — pulling latest…"
    git -C "$APP_DIR" fetch --all --quiet
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only
  else
    log "Cloning $REPO_URL into $APP_DIR"
    git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  fi
}

prepare_env() {
  cd "$APP_DIR"
  if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
      log "Creating .env from .env.example"
      cp .env.example .env
    else
      warn ".env.example not found. Creating minimal .env"
      cat > .env <<'EOF'
APP_ENV=prod
BOT_TOKEN=
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/botdb
REDIS_URL=redis://cache:6379/0
ADMIN_SECRET=change-me
ADMIN_ALLOWED_IDS=
CURRENCY=IRR
TZ=Asia/Tehran
WEB_BASE_URL=http://localhost:8080
BOT_WEBHOOK_SECRET=change-me
EOF
    fi
  fi

  # Prompt for key values if empty
  if ! grep -q '^BOT_TOKEN=' .env || [ -z "$(grep '^BOT_TOKEN=' .env | cut -d= -f2-)" ]; then
    ask "Enter your BOT_TOKEN" BOT_TOKEN
    sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=${BOT_TOKEN}|g" .env
  fi

  if ! grep -q '^ADMIN_ALLOWED_IDS=' .env || [ -z "$(grep '^ADMIN_ALLOWED_IDS=' .env | cut -d= -f2-)" ]; then
    ask "Enter admin numeric IDs (comma-separated)" ADMIN_ALLOWED_IDS
    sed -i "s|^ADMIN_ALLOWED_IDS=.*|ADMIN_ALLOWED_IDS=${ADMIN_ALLOWED_IDS}|g" .env
  fi

  # Fall back defaults for Currency/TZ if missing
  grep -q '^CURRENCY=' .env || echo "CURRENCY=IRR" >> .env
  grep -q '^TZ=' .env || echo "TZ=Asia/Tehran" >> .env
}

compose_up() {
  cd "$APP_DIR"
  command -v docker >/dev/null 2>&1 || { echo "docker not found"; exit 1; }
  log "Building & starting services with Docker Compose…"
  docker compose up -d --build
  log "Initializing database schema…"
  docker compose run --rm admin python scripts/init_db.py || true
}

setup_firewall() {
  if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q inactive; then
      warn "Skipping UFW enable (currently inactive). You can enable later: sudo ufw enable"
    fi
    sudo ufw allow 8080/tcp || true
    [ "$WITH_NGINX" = "1" ] && [ -n "$DOMAIN" ] && sudo ufw allow 'Nginx Full' || true
  fi
}

setup_nginx_ssl() {
  [ "$WITH_NGINX" = "1" ] || return 0
  if [ -z "$DOMAIN" ]; then
    err "WITH_NGINX=1 but DOMAIN is empty."
    exit 1
  fi

  if ! command -v nginx >/dev/null 2>&1; then
    log "Installing Nginx…"
    if command -v apt-get >/dev/null 2>&1; then
      if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; else SUDO=""; fi
      $SUDO apt-get install -y nginx
    else
      err "Nginx not available on this distro via this script. Install manually."
      exit 1
    fi
  fi

  local CONF="/etc/nginx/sites-available/telebot.conf"
  sudo bash -c "cat > $CONF" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:${ADMIN_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
  sudo ln -sf "$CONF" /etc/nginx/sites-enabled/telebot.conf
  sudo nginx -t
  sudo systemctl reload nginx

  if [ -n "$CERTBOT_EMAIL" ]; then
    if ! command -v certbot >/dev/null 2>&1; then
      log "Installing certbot…"
      if command -v apt-get >/dev/null 2>&1; then
        if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; else SUDO=""; fi
        $SUDO apt-get install -y certbot python3-certbot-nginx
      fi
    fi
    log "Requesting Let's Encrypt certificate for ${DOMAIN}…"
    sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$CERTBOT_EMAIL" || warn "Certbot failed; check DNS and try again."
  else
    warn "CERTBOT_EMAIL empty — skipping automatic SSL. You can run: sudo certbot --nginx -d ${DOMAIN}"
  fi
}

create_systemd_unit() {
  local UNIT="/etc/systemd/system/telebot-compose.service"
  if [ ! -f "$UNIT" ]; then
    log "Creating systemd unit to bring up Compose on boot…"
    sudo bash -c "cat > $UNIT" <<EOF
[Unit]
Description=telebot docker compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=${APP_DIR}
RemainAfterExit=true
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable telebot-compose.service
  fi
}

post_info() {
  cat <<EOF

====================================================
✅ Installation completed.

Admin Panel (direct, without Nginx):
  http://<SERVER-IP>:${ADMIN_PORT}/

Manage containers:
  cd ${APP_DIR}
  docker compose ps
  docker compose logs -f admin
  docker compose logs -f bot
  docker compose up -d --build
  docker compose down

If enabled Nginx/SSL, visit:
  https://${DOMAIN}/

To change env:
  nano ${APP_DIR}/.env
  docker compose up -d --build

Security tips:
  - Set strong ADMIN_SECRET / enable HTTPS if using a domain
  - Keep BOT_TOKEN private
  - Limit panel access (UFW, IP allowlist) if needed
====================================================
EOF
}

main() {
  # Unlike strict mode, we will prompt for REPO_URL if not passed,
  # but still require a non-empty value before cloning.
  if [ -z "${REPO_URL:-}" ]; then
    read -rp "Enter REPO_URL (e.g., https://github.com/user/repo.git): " REPO_URL || true
  fi
  if [ -z "${REPO_URL:-}" ]; then
    echo "REPO_URL is required. Exiting."; exit 1;
  fi

  install_prereqs
  install_docker
  clone_or_update_repo
  prepare_env
  compose_up
  setup_firewall
  setup_nginx_ssl || true
  create_systemd_unit || true
  post_info
}

main "$@"

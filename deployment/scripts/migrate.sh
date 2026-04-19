#!/bin/bash
# Migration helper: backup from old server, restore on new server.
# Usage:
#   On OLD server:  sudo bash migrate.sh backup
#   On NEW server:  sudo bash migrate.sh restore /tmp/chatbot_migrate.tar.gz

set -e

MODE="${1:-}"
PROJECT_DIR="/var/www/chatbot"
SERVER_USER="www-data"
BUNDLE="/tmp/chatbot_migrate.tar.gz"
DATA_FILE="/tmp/chatbot_data.json"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

case "$MODE" in
    backup)
        echo "[backup] Dumping data from $PROJECT_DIR"
        cd "$PROJECT_DIR"
        export DJANGO_SETTINGS_MODULE=config.settings.production

        sudo -u "$SERVER_USER" -E "$PROJECT_DIR/venv/bin/python" manage.py dumpdata \
            --natural-foreign --natural-primary \
            --exclude contenttypes \
            --exclude auth.permission \
            --exclude admin.logentry \
            --exclude sessions \
            --indent 2 \
            -o "$DATA_FILE"

        chown "$SERVER_USER":"$SERVER_USER" "$DATA_FILE"

        echo "[backup] Bundling media + data -> $BUNDLE"
        tar czf "$BUNDLE" \
            -C "$PROJECT_DIR" media \
            -C /tmp "$(basename "$DATA_FILE")"

        echo "[backup] Done. Copy to new server:"
        echo "  scp $BUNDLE root@43.242.224.74:/tmp/"
        ;;

    restore)
        ARCHIVE="${2:-$BUNDLE}"
        if [ ! -f "$ARCHIVE" ]; then
            echo "Archive not found: $ARCHIVE"
            exit 1
        fi

        echo "[restore] Extracting $ARCHIVE"
        RESTORE_DIR=$(mktemp -d)
        tar xzf "$ARCHIVE" -C "$RESTORE_DIR"

        echo "[restore] Copying media files"
        mkdir -p "$PROJECT_DIR/media"
        cp -r "$RESTORE_DIR/media/." "$PROJECT_DIR/media/"
        chown -R "$SERVER_USER":"$SERVER_USER" "$PROJECT_DIR/media"

        echo "[restore] Loading data into PostgreSQL"
        cd "$PROJECT_DIR"
        export DJANGO_SETTINGS_MODULE=config.settings.production
        sudo -u "$SERVER_USER" -E "$PROJECT_DIR/venv/bin/python" manage.py migrate --noinput
        sudo -u "$SERVER_USER" -E "$PROJECT_DIR/venv/bin/python" manage.py loaddata \
            "$RESTORE_DIR/chatbot_data.json"

        echo "[restore] Restarting chatbot service"
        systemctl restart chatbot

        rm -rf "$RESTORE_DIR"
        echo "[restore] Done. Verify: curl http://localhost/health"
        ;;

    *)
        echo "Usage:"
        echo "  On OLD server:  sudo bash migrate.sh backup"
        echo "  On NEW server:  sudo bash migrate.sh restore [/tmp/chatbot_migrate.tar.gz]"
        exit 1
        ;;
esac

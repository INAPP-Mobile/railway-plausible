#!/bin/sh
set -e

# Simplified entrypoint: start clickhouse-server, wait for /ping, then start healthcat

# Setup directories
DATA_DIR="/var/lib/clickhouse"
TMP_DIR="/var/lib/clickhouse/tmp"
USER_PATH="/var/lib/clickhouse/user_files"
LOG_PATH="/var/log/clickhouse-server/clickhouse-server.log"
LOG_DIR="/var/log/clickhouse-server"

mkdir -p "$DATA_DIR" "$TMP_DIR" "$USER_PATH" "$LOG_DIR" "$DATA_DIR/metadata" "$DATA_DIR/tmp"

# Handle user setup
CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-}"
CLICKHOUSE_DB="${CLICKHOUSE_DB:-default}"

if [ -n "$CLICKHOUSE_PASSWORD" ]; then
    cat > /etc/clickhouse-server/users.d/default-user.xml <<EOF
<clickhouse>
  <users>
    <default remove="remove"></default>
    <${CLICKHOUSE_USER}>
      <password>${CLICKHOUSE_PASSWORD}</password>
      <networks><ip>::/0</ip></networks>
      <profile>default</profile>
      <quota>default</quota>
    </${CLICKHOUSE_USER}>
  </users>
</clickhouse>
EOF
fi

# Start clickhouse-server in background
echo "Starting clickhouse-server..."
clickhouse-server --config-file=/etc/clickhouse-server/config.xml &
CH_PID=""

# Wait for pid file
for i in $(seq 1 30); do
    PID_FILE="/tmp/clickhouse-server/clickhouse-server.${CLICKHOUSE_PORT:-8123}.pid" 2>/dev/null
    if [ -f "/var/run/clickhouse-server/clickhouse-server.pid" ]; then
        CH_PID=$(cat /var/run/clickhouse-server/clickhouse-server.pid 2>/dev/null || echo "")
        [ -n "$CH_PID" ] && break
    fi
    sleep 2
done

# Wait for ping to respond
echo "Waiting for clickhouse-server to accept connections..."
for i in $(seq 1 60); do
    if wget -qO- http://127.0.0.1:8123/ping 2>/dev/null | grep -q "Ok"; then
        echo "ClickHouse ready"
        break
    fi
    sleep 2
done

# Create database if specified
if [ -n "$CLICKHOUSE_DB" ] && [ "$CLICKHOUSE_DB" != "default" ]; then
    echo "Creating database: $CLICKHOUSE_DB"
    clickhouse-client --host 127.0.0.1 -u "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" \
        -q "CREATE DATABASE IF NOT EXISTS $CLICKHOUSE_DB" 2>/dev/null || true
fi

# Start healthcat in background
echo "Starting healthcat proxy..."
python3 /healthcat.py &
HC_PID=$!

echo "ClickHouse and healthcat started. Monitoring..."
# Wait for either process to exit
wait $CH_PID

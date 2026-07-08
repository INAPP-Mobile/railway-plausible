#!/bin/sh
set -e

# Setup directories
DATA_DIR="/var/lib/clickhouse"
LOG_DIR="/var/log/clickhouse-server"

for d in "$DATA_DIR" "$DATA_DIR/metadata" "$DATA_DIR/tmp" "$DATA_DIR/user_files" "$LOG_DIR"; do
    mkdir -p "$d"
done

# Get user/env config
CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-}"
CLICKHOUSE_DB="${CLICKHOUSE_DB:-default}"

# Write user config if password is set
if [ -n "$CLICKHOUSE_PASSWORD" ]; then
    cat > /tmp/users.xml <<EOF
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
    cp /tmp/users.xml /etc/clickhouse-server/users.d/default-user.xml
fi

# Start clickhouse-server in background (now on port 8124)
echo "Starting clickhouse-server (port 8124)..."
clickhouse-server --config-file=/etc/clickhouse-server/config.xml > /dev/null 2>&1 &
CH_PID=$!

# Wait for clickhouse /ping to respond
echo "Waiting for clickhouse to be ready..."
for i in $(seq 1 60); do
    if wget -qO- http://127.0.0.1:8124/ping 2>/dev/null | grep -q "Ok"; then
        echo "ClickHouse ready (port 8124)"
        break
    fi
    sleep 2
done

# Create database if specified
if [ "$CLICKHOUSE_DB" != "default" ]; then
    echo "Creating database: $CLICKHOUSE_DB"
    clickhouse-client --host 127.0.0.1 --port 8124 -u "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" \
        -q "CREATE DATABASE IF NOT EXISTS $CLICKHOUSE_DB" 2>/dev/null || true
fi

# Start healthcat proxy on port 8123
echo "Starting healthcat proxy (port 8123)..."
python3 /healthcat.py > /dev/null 2>&1 &
HC_PID=$!

echo "All services started"
# Keep container alive and wait for both processes
wait $CH_PID $HC_PID

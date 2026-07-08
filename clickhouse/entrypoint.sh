#!/bin/sh
# Custom entrypoint: start clickhouse-server directly, then healthcat proxy

set -e

# Create required directories
mkdir -p /var/lib/clickhouse/data /var/lib/clickhouse/metadata /var/lib/clickhouse/tmp /var/lib/clickhouse/user_files /var/log/clickhouse-server

# Handle user/password setup
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

# Start clickhouse-server in background (port 8124)
echo "Starting clickhouse-server on port 8124..."
clickhouse-server --config-file=/etc/clickhouse-server/config.xml >> /tmp/ch.log 2>&1 &
CH_PID=$!

# Wait for clickhouse to be ready
echo "Waiting for clickhouse /ping..."
for i in $(seq 1 90); do
    if wget -qO- http://127.0.0.1:8124/ping 2>/dev/null | grep -q "Ok"; then
        echo "ClickHouse ready!"
        break
    fi
    sleep 2
done

# Create database if needed
if [ "$CLICKHOUSE_DB" != "default" ]; then
    echo "Creating database '$CLICKHOUSE_DB'..."
    clickhouse-client --host 127.0.0.1 --port 8124 -u "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" \
        -q "CREATE DATABASE IF NOT EXISTS $CLICKHOUSE_DB" 2>/dev/null || true
fi

# Start healthcat proxy on port 8123
echo "Starting healthcat proxy on port 8123..."
python3 /healthcat.py >> /tmp/hc.log 2>&1 &
HC_PID=$!

echo "All services started. Waiting..."
wait

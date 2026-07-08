FROM docker.io/clickhouse/clickhouse-server:24.12-alpine

# ClickHouse server optimized for low-resource environments
# Config files from Plausible CE project
COPY logs.xml /etc/clickhouse-server/config.d/logs.xml
COPY ipv4-only.xml /etc/clickhouse-server/config.d/ipv4-only.xml
COPY low-resources.xml /etc/clickhouse-server/config.d/low-resources.xml
COPY default-profile-low-resources-overrides.xml /etc/clickhouse-server/users.d/default-profile-low-resources-overrides.xml

EXPOSE 8123 9000 8080

# Install tools for healthcheck proxy
RUN apk add --no-cache python3 curl

# healthcat.py: tiny HTTP server on :8080 that proxies /api/health to clickhouse /ping
COPY healthcat.py /healthcat.py
RUN chmod +x /healthcat.py

# Start clickhouse and healthcat in background, wait for both
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

HEALTHCHECK --interval=15s --timeout=5s --start-period=120s --retries=10 \
  CMD curl -sf http://127.0.0.1:8080/api/health -o /dev/null || exit 1

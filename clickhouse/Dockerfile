FROM docker.io/clickhouse/clickhouse-server:24.12-alpine

# ClickHouse server optimized for low-resource environments
# Config files from Plausible CE project

COPY logs.xml /etc/clickhouse-server/config.d/logs.xml
COPY ipv4-only.xml /etc/clickhouse-server/config.d/ipv4-only.xml
COPY low-resources.xml /etc/clickhouse-server/config.d/low-resources.xml
COPY default-profile-low-resources-overrides.xml /etc/clickhouse-server/users.d/default-profile-low-resources-overrides.xml

EXPOSE 8123 9000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 -O - http://127.0.0.1:8123/ping || exit 1

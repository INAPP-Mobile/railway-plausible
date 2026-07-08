FROM clickhouse/clickhouse-server:24.12-alpine

# ClickHouse config for Plausible CE on Railway
COPY config.d/ /etc/clickhouse-server/config.d/
COPY users.d/  /etc/clickhouse-server/users.d/

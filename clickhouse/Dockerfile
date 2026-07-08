FROM docker.io/clickhouse/clickhouse-server:24.12-alpine

# ClickHouse server optimized for low-resource environments
# Config files from Plausible CE project
COPY logs.xml /etc/clickhouse-server/config.d/logs.xml
COPY ipv4-only.xml /etc/clickhouse-server/config.d/ipv4-only.xml
COPY low-resources.xml /etc/clickhouse-server/config.d/low-resources.xml
COPY default-profile-low-resources-overrides.xml /etc/clickhouse-server/users.d/default-profile-low-resources-overrides.xml

# Install tools for healthcheck proxy
RUN apk add --no-cache python3 curl

# healthcat.py: tiny HTTP server on :8123 that responds 200 to /api/health
# and proxies other requests to clickhouse on :8124
COPY healthcat.py /healthcat.py
RUN chmod +x /healthcat.py

# Move clickhouse HTTP from 8123 to 8124
RUN sed -i 's|<http_port>8123</http_port>|<http_port>8124</http_port>|' /etc/clickhouse-server/config.xml

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8123 8124 9000

HEALTHCHECK --interval=15s --timeout=5s --start-period=120s --retries=10 \
  CMD curl -sf http://127.0.0.1:8123/api/health -o /dev/null || exit 1

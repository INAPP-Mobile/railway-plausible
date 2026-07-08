FROM ghcr.io/plausible/community-edition:v3.2.1

ENV PORT=8000

# Run database migrations then start the release
# entrypoint.sh: "db migrate" runs /app/migrate.sh, "run" starts /app/bin/plausible
CMD ["/bin/sh", "-c", "/entrypoint.sh db migrate && /entrypoint.sh run"]

HEALTHCHECK --interval=15s --timeout=10s --start-period=180s --retries=10 \
  CMD wget --no-verbose --tries=1 -O - http://127.0.0.1:8000/api/health 2>/dev/null || exit 1

FROM ghcr.io/plausible/community-edition:v3.2.1

ENV PORT=8000

# Healthcheck Plausible API
HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=10 \
  CMD wget --no-verbose --tries=1 -O - http://127.0.0.1:8000/api/health 2>/dev/null || exit 1

# Run migrations then start the server
CMD ["/bin/sh", "-c", "/entrypoint.sh db migrate && /entrypoint.sh run"]
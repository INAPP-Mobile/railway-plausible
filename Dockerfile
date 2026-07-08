FROM ghcr.io/plausible/community-edition:v3.2.1

ENV PORT=8000

HEALTHCHECK --interval=15s --timeout=10s --start-period=120s --retries=10 \
  CMD wget --no-verbose --tries=1 -O - http://127.0.0.1:8000/api/health 2>/dev/null || exit 1

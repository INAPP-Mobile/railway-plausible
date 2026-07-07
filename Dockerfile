FROM ghcr.io/plausible/community-edition:v3.2.1

# Plausible Community Edition Railway
# Uses official image directly
# All configuration goes through environment variables

EXPOSE 8000

# Default runtime configuration
ENV PORT=8000


# upstream image entrypoint handles setup server start
# Command format: /entrypoint.sh createdb && /entrypoint.sh migrate && /entrypoint.sh run
CMD ["sh", "-c", "/entrypoint.sh createdb && /entrypoint.sh migrate && /entrypoint.sh run"]

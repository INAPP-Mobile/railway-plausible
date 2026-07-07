FROM ghcr.io/plausible/community-edition:v3.2.1

# Plausible Community Edition Railway
# Uses official image directly
# All configuration goes through environment variables

EXPOSE 8000

# Default runtime configuration
ENV PORT=8000


# Base image entrypoint handles full lifecycle (run, createdb, migrate handled by upstream)
CMD []

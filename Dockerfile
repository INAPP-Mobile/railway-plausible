FROM ghcr.io/plausible/community-edition:v3.2.1

# Plausible Community Edition on Railway
# Uses the official CE image directly
# All configuration goes through environment variables

EXPOSE 8000

# The upstream image entrypoint handles DB setup and server start
# Command format: /entrypoint.sh db createdb && /entrypoint.sh db migrate && /entrypoint.sh run
CMD ["sh", "-c", "/entrypoint.sh db createdb && /entrypoint.sh db migrate && /entrypoint.sh run"]

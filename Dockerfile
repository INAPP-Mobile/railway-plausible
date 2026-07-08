FROM ghcr.io/plausible/community-edition:v3.2.1

ENV PORT=8000

# Run database migrations then start the release
# entrypoint.sh: "db migrate" runs /app/migrate.sh, "run" starts /app/bin/plausible
CMD ["/bin/sh", "-c", "/entrypoint.sh db migrate && /entrypoint.sh run"]

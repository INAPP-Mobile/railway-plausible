FROM ghcr.io/plausible/community-edition:v3.2.1

# Plausible Community Edition Railway
EXPOSE 8000
ENV PORT=8000

# Run migrations then start server
CMD ["/bin/sh", "-c", "/entrypoint.sh db migrate && /entrypoint.sh run"]

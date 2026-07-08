FROM ghcr.io/plausible/community-edition:v3.2.1

ENV PORT=8000

# Run migrations then start server
CMD ["/entrypoint.sh", "start"]